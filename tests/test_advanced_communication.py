"""Test the AdvancedCommunication class"""

from unittest.mock import MagicMock, patch

import pytest
from src.controls import AdvancedCommunication

# pylint: disable=redefined-outer-name
# pylint: disable=protected-access

# ---------------------------------------------------------------------------------------
# Setup

DEVICE = MagicMock()
DEVICE.device_id = "RP2040_1"
DEVICE.pca = True

NOMINAL_CONFIG_DICT = {
    "retries": 3,
    "connection_cycles": 2,
    "power_cycles": 2,
    "hb_send_msg": "ping",
    "hb_receive_msg": "pong",
}


@pytest.fixture
def ac() -> AdvancedCommunication:
    """Construct an instance of the AdvancedCommunication clas"""
    return AdvancedCommunication(NOMINAL_CONFIG_DICT, DEVICE)


# ---------------------------------------------------------------------------------------
# test send() method

# Four branches:
#    - first / secondary send success
#    - first send failure
#    - secondary send failure


@pytest.mark.parametrize("secondary_send", [(False), (True)])
def test_send_success(ac: AdvancedCommunication, secondary_send: bool) -> None:
    """Test a successful send"""
    ac.device = MagicMock()
    ac.device.read_and_write.return_value = True
    with patch("src.controls.logger") as mock_logger:
        result = ac.send("send_msg", "receive_msg", secondary_send)
        assert result is True
        assert mock_logger.info.call_count == 1
        ac.device.read_and_write.assert_called_once_with("send_msg", "receive_msg")


@pytest.mark.parametrize("secondary_send", [(False), (True)])
def test_send_failure(ac: AdvancedCommunication, secondary_send: bool) -> None:
    """Test a failed sends"""
    ac.device = MagicMock()
    ac.device.read_and_write.return_value = False
    with patch("src.controls.logger") as mock_logger:
        result = ac.send("send_msg", "receive_msg", secondary_send)
        log_msgs = mock_logger.info.call_args_list
        assert result is False
        assert mock_logger.info.call_count == 2
        ac.device.read_and_write.assert_called_once_with("send_msg", "receive_msg")
        if secondary_send:
            assert (
                "connection was recovered with heartbeat, but failed on"
                in log_msgs[1].args[0]
            )
        else:
            assert "Continuing to connection recovery" in log_msgs[1].args[0]


# ---------------------------------------------------------------------------------------
# test _retries() method

# Two branches:
#   - retry gets a confirmed output
#   - retry does not get a confirmed output
#   - verify call count to read_and_write if all fail


@pytest.mark.parametrize(
    "confirmed, expected_result",
    [
        (True, True),
        (False, False),
    ],
)
def test_retries(
    ac: AdvancedCommunication, confirmed: bool, expected_result: bool
) -> None:
    """Test _retries() method"""
    ac.device = MagicMock()
    ac.device.read_and_write.return_value = confirmed
    result = ac._retries("ping", "pong")

    if confirmed:
        ac.device.read_and_write.assert_called_once_with("ping", "pong")
    else:
        ac.device.read_and_write.assert_any_call("ping", "pong")
        assert ac.device.read_and_write.call_count == ac.retries

    assert result is expected_result


# ---------------------------------------------------------------------------------------
# test _software_cycle() method

# Two branches:
#   - software cycle gets a confirmed output
#   - software cycle does not get a confirmed output
#   - verify call count to connect / disconnect if all fail


@pytest.mark.parametrize(
    "confirmed, expected_result",
    [
        (True, True),
        (False, False),
    ],
)
def test_software_cycle(
    ac: AdvancedCommunication, confirmed: bool, expected_result: bool
) -> None:
    """Test _software_cycle() method"""
    ac.device = MagicMock()
    ac.device.read_and_write.return_value = confirmed

    result = ac._software_cycle()

    if confirmed:
        ac.device.disconnect.assert_called_once()
        ac.device.connect.assert_called_once()
        ac.device.read_and_write.assert_called_once()
        assert result is expected_result
    else:
        assert ac.device.disconnect.call_count == ac.connection_cycles
        assert ac.device.connect.call_count == ac.connection_cycles
        assert ac.device.read_and_write.call_count == ac.connection_cycles
        assert result is expected_result


# ---------------------------------------------------------------------------------------
# test _power_cycle() method

# branches:
#   - pca is True (power cycling is available)
#       - power cycle gets a confirmed output
#       - power cycle does not get a confirmed output
#       - verify call count to connect / disconnect if all fail
#       - exception while executing power cycle
#   - pca is False (power cycling is unavailable)


@pytest.mark.parametrize(
    "pca, confirmed, expected_result",
    [
        (False, None, False),
        (True, True, True),
        (True, False, False),
        (True, False, False),
    ],
)
def test_power_cycle(
    ac: AdvancedCommunication, pca: bool, confirmed: bool, expected_result: bool
) -> None:
    """Test power cycling when it is available and unavailable"""
    ac.device = MagicMock()
    ac.device.read_and_write.return_value = confirmed

    if pca:
        ac.device.pca = True
    else:
        ac.device.pca = False

    result = ac._power_cycle()

    if pca is False:
        assert result is expected_result

    if pca:
        if confirmed:
            ac.device.read_and_write.assert_called_once()
            assert result is expected_result
        if confirmed is False:
            assert ac.device.read_and_write.call_count == ac.power_cycles


def test_power_cycle_exception(ac: AdvancedCommunication) -> None:
    """Test raised exception catch during power cycle"""
    ac.device = MagicMock()
    ac.device.read_and_write.side_effect = Exception("fail")
    with patch("src.controls.logger") as mock_logger:

        result = ac._power_cycle()

        assert mock_logger.error.call_count == ac.power_cycles
        assert result is False


# ---------------------------------------------------------------------------------------
# test advanced_connection() method

# Branches:
#   - Nominal recovery
#   - Retries recovery
#   - software cycle recovery
#       - secondary send success
#       - secondary send failure
#   - power cycle recovery
#       - secondary send success
#       - secondary send failure


@pytest.mark.parametrize(
    "send, retries, sc, pc",
    [
        ([True, None], False, False, False),
        ([False, None], True, False, False),
        ([False, True], False, True, False),
        ([False, False], False, True, False),
        ([False, True], False, False, True),
        ([False, False], False, False, True),
    ],
)
def test_advanced_connection(
    ac: AdvancedCommunication, send: list, retries: bool, sc: bool, pc: bool
) -> None:
    """Test the advanced connection method"""
    ac.send = MagicMock(side_effect=send)
    ac._retries = MagicMock(return_value=retries)
    ac._software_cycle = MagicMock(return_value=sc)
    ac._power_cycle = MagicMock(return_value=pc)

    results_dict = ac.advanced_connection("ping", "pong")

    if retries | send[0]:
        assert results_dict["confirmed"] is True
    else:
        assert results_dict["confirmed"] == send[1]
    assert results_dict["nominal"] == send[0]
    assert results_dict["retries"] == retries
    assert results_dict["software_cycle"] == sc
    assert results_dict["power_cycle"] == pc

    if send[0]:
        ac.send.assert_called_once()
        ac._retries.assert_not_called()
        ac._software_cycle.assert_not_called()
        ac._power_cycle.assert_not_called()

    if retries:
        ac.send.assert_called_once()
        ac._retries.assert_called_once()
        ac._software_cycle.assert_not_called()
        ac._power_cycle.assert_not_called()

    if sc:
        assert ac.send.call_count == 2
        ac._retries.assert_called_once()
        ac._software_cycle.assert_called_once()
        ac._power_cycle.assert_not_called()

    if pc:
        assert ac.send.call_count == 2
        ac._retries.assert_called_once()
        ac._software_cycle.assert_called_once()
        ac._power_cycle.assert_called_once()


# ---------------------------------------------------------------------------------------
