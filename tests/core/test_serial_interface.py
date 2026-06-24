"""Test the SerialInterface Class"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from serial import SerialException
from hilsim.core.controls import SerialInterface

# pylint: disable=redefined-outer-name

# ---------------------------------------------------------------------------------------
# setup

@pytest.fixture
def device_name() -> str: 
    """Return the device name"""
    return "device_1"

@pytest.fixture
def base_config(device_config: dict, device_name: str) -> None: 
    """Create a nominal config dict for real serial connection"""
    config_dict = device_config["devices"][device_name]
    config_dict["sim"] = False
    config_dict["super_sim"] = False
    return config_dict

@pytest.fixture
def sim_config(base_config: dict) -> dict:
    """Create fixture with sim config_dict (sim connection)"""
    copy_config = {**base_config, "sim": True, "super_sim": False}
    return copy_config


@pytest.fixture
def super_sim_config(base_config: dict) -> dict:
    """Create fixture with super_sum config_dict (super sim connection)"""
    copy_config = {**base_config, "super_sim": True, "sim": False}
    return copy_config


@pytest.fixture
def real_serial_interface(base_config: dict, device_name: str) -> SerialInterface:
    """Construct instance of a real SerialInterface connection"""
    return SerialInterface(base_config, device_name)

@pytest.fixture
def sim_serial_interface(sim_config: dict, device_name: str) -> SerialInterface:
    """Construct instance of a real SerialInterface connection"""
    return SerialInterface(sim_config, device_name)


@pytest.fixture
def super_sim_serial_interface(super_sim_config: dict, device_name: str) -> SerialInterface:
    """Construct instance of a real SerialInterface connection"""
    return SerialInterface(super_sim_config, device_name)


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

def test_initialize_connection_real(base_config: dict, real_serial_interface: SerialInterface) -> None: 
    """Test initializing a real connection """
    with (patch("hilsim.core.controls.logger"),
          patch("hilsim.core.controls.serial.Serial") as mock_serial):
        real_serial_interface.connect() 
        port = base_config["device_ID"]
        baudrate = base_config["baud_rate"]
        timeout = base_config["time_out"]
    mock_serial.assert_called_once_with(port=port, baudrate=baudrate, timeout=timeout)
    assert real_serial_interface.connected is True
    assert isinstance(real_serial_interface.ser, MagicMock)

def test_initialize_connection_sim(base_config: dict, sim_serial_interface: SerialInterface) -> None: 
    """Test initializing a real connection """
    with (patch("hilsim.core.controls.logger"),
          patch("hilsim.core.controls.serial.Serial") as mock_serial):
        sim_serial_interface.connect() 
        port = base_config["fake_device_ID"]
        baudrate = base_config["baud_rate"]
        timeout = base_config["time_out"]
    mock_serial.assert_called_once_with(port=port, baudrate=baudrate, timeout=timeout)
    assert sim_serial_interface.connected is True
    assert isinstance(sim_serial_interface.ser, MagicMock)

def test_initialize_connection_failure(real_serial_interface: SerialInterface) -> None:
    """Test the failure path of connection"""
    with patch(
        "hilsim.core.controls.serial.Serial", side_effect=SerialException("failure_test")
    ), patch("hilsim.core.controls.logger") as mock_logger:

        result = real_serial_interface.connect()
    mock_logger.error.assert_called_once()
    assert real_serial_interface.connected is False
    assert result is False


def test_initialize_connection_super_sim(
    super_sim_serial_interface: SerialInterface,
) -> None:
    """Test connecting in the super sim case"""
    fake_serial_instance = MagicMock()
    with patch(
        "hilsim.core.controls.FakeSerial", return_value=fake_serial_instance
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

    with patch("hilsim.core.controls.logger") as mock_logger:
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
    with patch("hilsim.core.controls.datetime") as mock_datetime, patch(
        "hilsim.core.controls.logger"
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
    with patch("hilsim.core.controls.logger") as mock_logger:
        result = real_serial_interface.read_and_write("ping", "pong")

    mock_logger.error.assert_called_once()
    assert result is False

# ---------------------------------------------------------------------------------------
