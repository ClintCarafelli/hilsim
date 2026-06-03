"""Test the SerialInterface Class"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from serial import SerialException
from src.controls import SerialInterface

# pylint: disable=redefined-outer-name

# ---------------------------------------------------------------------------------------
# setup

DEVICE_NAME = "RP2040_1"
NOMINAL_CONFIG_DICT = {
    "sim": False,
    "super_sim": False,
    "super_sim_fr": 0,
    "baud_rate": 115200,
    "device_ID": "/dev/ttyACM0",
    "fake_device_ID": "/tmp/ttyVirtual1",
    "time_out": 1,
    "read_time": 0.5,
    "hb_send_msg": "ping",
    "hb_receive_msg": "pong",
}


@pytest.fixture
def base_config() -> dict:
    """Create fixture with nominal config_dict (real connection)"""
    return NOMINAL_CONFIG_DICT


@pytest.fixture
def sim_config(base_config: dict) -> dict:
    """Create fixture with sim config_dict (sim connection)"""
    copy_config = {**base_config, "sim": True}
    return copy_config


@pytest.fixture
def super_sim_config(base_config: dict) -> dict:
    """Create fixture with super_sum config_dict (super sim connection)"""
    copy_config = {**base_config, "super_sim": True}
    return copy_config


@pytest.fixture
def real_serial_interface(base_config: dict) -> SerialInterface:
    """Construct instance of a real SerialInterface connection"""
    return SerialInterface(base_config, DEVICE_NAME)


@pytest.fixture
def super_sim_serial_interface(super_sim_config: dict) -> SerialInterface:
    """Construct instance of a real SerialInterface connection"""
    return SerialInterface(super_sim_config, DEVICE_NAME)


# ---------------------------------------------------------------------------------------
# Test connect() method

# device id Branches:
#   - device_id is fake device_id
#   - device_id is real device_id

# If is not super sim branches:
#    - successfully call serial.Serial
#    - fail on call to serial.Serial

# If super sim:
#   - construct instance of FakeSerial


@pytest.mark.parametrize(
    "sim, expected_device", [(True, "/tmp/ttyVirtual1"), (False, "/dev/ttyACM0")]
)
def test_initialize_connection(
    real_serial_interface: SerialInterface, sim: bool, expected_device: str
) -> None:
    """Test successful connection paths for both a real and sim sensor. Using
    parametrization severly reduces code redundancy here"""
    real_serial_interface.sim = sim
    fake_serial_instance = MagicMock()

    with patch(
        "src.controls.serial.Serial", return_value=fake_serial_instance
    ) as mock_serial:
        result = real_serial_interface.connect()

    mock_serial.assert_called_once_with(
        port=expected_device,
        baudrate=real_serial_interface.baud_rate,
        timeout=real_serial_interface.time_out,
    )

    assert real_serial_interface.ser is fake_serial_instance
    assert real_serial_interface.connected is True
    assert result is True


def test_initialize_connection_failure(real_serial_interface: SerialInterface) -> None:
    """Test the failure path of connection"""
    with patch(
        "src.controls.serial.Serial", side_effect=SerialException("failure_test")
    ), patch("src.controls.logger") as mock_logger:

        result = real_serial_interface.connect()
    mock_logger.error.assert_called_once()
    assert real_serial_interface.connected is False
    assert result is False


def test_super_sim_initialize_connection(
    super_sim_serial_interface: SerialInterface,
) -> None:
    """Test connecting in the super sim case"""
    fake_serial_instance = MagicMock()
    with patch(
        "src.controls.FakeSerial", return_value=fake_serial_instance
    ) as mock_fake_serial:
        super_sim_serial_interface.connect()

    mock_fake_serial.assert_called_once_with(
        super_sim_serial_interface.super_sim_fr,
        super_sim_serial_interface.read_time,
        super_sim_serial_interface.hb_sm,
        super_sim_serial_interface.hb_rm,
    )
    assert super_sim_serial_interface.ser is fake_serial_instance


# ---------------------------------------------------------------------------------------
# Test the disconnect() method

# Using real_serial_interface as the natural default here since behavior does not branch
# based on real/sim/super_sim behavior


def test_disconnect_success(real_serial_interface: SerialInterface) -> None:
    """Test a successful disconnection"""
    real_serial_interface.ser = MagicMock()
    real_serial_interface.disconnect()
    real_serial_interface.ser.close.assert_called_once_with()


def test_disconnect_failure(real_serial_interface: SerialInterface) -> None:
    """Test a successful disconnection"""
    real_serial_interface.ser = MagicMock()
    real_serial_interface.ser.close.side_effect = SerialException("boom")

    with patch("src.controls.logger") as mock_logger:
        real_serial_interface.disconnect()

    mock_logger.info.assert_called_once()
    mock_logger.error.assert_called_once()


# ---------------------------------------------------------------------------------------
# Test the read_and_write() method

# Branching:
#   - calls to ser do not error
#       - correct return message is recieved
#       - no/incorrect return message is recieved
#   - calls to ser error
#       - Catch SerialException


@pytest.mark.parametrize(
    "serial_response, expected_result, expect_error_log",
    [
        (b"pong", True, False),
        (b"", False, True),
    ],
)

# Using real_serial_interface as the natural default here since behavior doesn't
# branch based on real/sim/super_sim
def test_read_and_write(
    real_serial_interface: SerialInterface,
    serial_response: bytes,
    expected_result: bool,
    expect_error_log: bool,
) -> None:
    """Test both branches when ser calls do not error: correct response and incorrect response"""
    start_time = datetime(2024, 1, 1, 0, 0, 0)

    real_serial_interface.ser = MagicMock()
    real_serial_interface.ser.readline.return_value = serial_response

    times = [
        start_time,
        start_time + timedelta(seconds=0.001),
        start_time + timedelta(seconds=10000),
    ]
    with patch("src.controls.datetime") as mock_datetime, patch(
        "src.controls.logger"
    ) as mock_logger:
        mock_datetime.now.side_effect = times
        result = real_serial_interface.read_and_write("ping", "pong")

    assert result is expected_result
    real_serial_interface.ser.write.assert_called_once_with(b"ping")
    if expect_error_log:
        mock_logger.error.assert_called_once()
    else:
        mock_logger.error.assert_not_called()


def test_read_and_write_serial_exceptions(
    real_serial_interface: SerialInterface,
) -> None:
    """Test catching SerialExceptions"""
    real_serial_interface.ser = MagicMock()
    real_serial_interface.ser.write.side_effect = SerialException("fail here")
    with patch("src.controls.logger") as mock_logger:
        result = real_serial_interface.read_and_write("ping", "pong")

    mock_logger.error.assert_called_once()
    assert result is False


# ---------------------------------------------------------------------------------------
