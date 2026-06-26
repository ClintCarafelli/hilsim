"""Test the FakeSerial class"""

from unittest.mock import MagicMock, patch

import pytest
from src.hilsim.core.controls import FakeSerial

# pylint: disable=redefined-outer-name

# ---------------------------------------------------------------------------------------
# Setup


@pytest.fixture
def base_config(device_config: dict) -> dict:
    """Create a dictonary of basic things needed for fakeserial construction"""
    return device_config["devices"]["device_1"]


@pytest.fixture
def zero_failure(base_config: dict) -> dict:
    """Create a dictonary that guarantees success in super_sim mode"""
    copy_config = {**base_config, "super_sim_fr": 0}
    return copy_config


@pytest.fixture
def always_failure(base_config: dict) -> dict:
    """Create a dictonary that holds guaranteed failure in super_sim mode"""
    copy_config = {**base_config, "super_sim_fr": 1}
    return copy_config


@pytest.fixture
def fake_serial_fail(always_failure: dict) -> FakeSerial:
    """Construct a FakeSerial instance that always fails on readline"""
    return FakeSerial(
        always_failure["super_sim_fr"],
        always_failure["read_time"],
        always_failure["hb_send_msg"],
        always_failure["hb_receive_msg"],
    )


@pytest.fixture
def fake_serial_success(zero_failure: dict) -> FakeSerial:
    """Construct a FakeSerial instance that never fails on readline"""
    return FakeSerial(
        zero_failure["super_sim_fr"],
        zero_failure["read_time"],
        zero_failure["hb_send_msg"],
        zero_failure["hb_receive_msg"],
    )

# ---------------------------------------------------------------------------------------
# Test write() method


# Note: using success instance of FakeSerial as defualt because behavior does not branch
def test_write(fake_serial_success: FakeSerial) -> None:
    """Test write method"""
    fake_serial_success.write("message".encode())
    assert fake_serial_success.msg == "message".encode()


# ---------------------------------------------------------------------------------------
# Test readline() method

# Two branches:
#   - successfully readline
#   - fail to read line


@patch("src.hilsim.core.controls.time.sleep")
def test_readline_failure(mock_sleep: MagicMock, fake_serial_fail: FakeSerial) -> None:
    """Test a readline failure (result is empty string encoded)"""
    result = fake_serial_fail.readline()
    assert result == "".encode()
    mock_sleep.assert_called_once_with(fake_serial_fail.read_time * 0.01)


@patch("src.hilsim.core.controls.random")
def test_readline_succeed(
    mock_random: MagicMock, fake_serial_success: FakeSerial
) -> None:
    """Test a readline success (returning correct encoded message)"""
    mock_random.return_value = 0
    fake_serial_success.msg = "message".encode()
    assert fake_serial_success.readline() == "message".encode()
    fake_serial_success.msg = fake_serial_success.hb_send_msg.encode()
    assert fake_serial_success.readline() == fake_serial_success.hb_receive_msg.encode()


# ---------------------------------------------------------------------------------------
# Test close() method

# Note: testing with sucess instance of FakeSerial as default becaue behavior does
# not branch based on the failure rate


def test_close(fake_serial_success: FakeSerial) -> None:
    """Test the close method"""
    fake_serial_success.close()


# ---------------------------------------------------------------------------------------
