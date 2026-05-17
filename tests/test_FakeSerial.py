import pytest
from unittest.mock import patch
from src.RP2040 import FakeSerial

@pytest.fixture
def base_config():
    return {"RP_connection":{
                "super_sim_fr": 1,
                "read_time": 0.5,
                "hb_send_msg": "ping",
                "hb_receive_msg": "pong"}}

@pytest.fixture
def zero_failure(base_config):
    base_config["RP_connection"]["super_sim_fr"] = 0
    return base_config

@pytest.fixture
def always_failure(base_config):
    base_config["RP_connection"]["super_sim_fr"] = 1
    return base_config

@pytest.fixture
def FakeSerial_fail(always_failure):
    return FakeSerial(always_failure)

@pytest.fixture
def FakeSerial_succeed(zero_failure):
    return FakeSerial(zero_failure)

# only testing with succeed case since it doesn't branch and 
# suceed is the natural default
def test_write_succeed(FakeSerial_succeed):
    FakeSerial_succeed.write("message".encode())
    assert FakeSerial_succeed.msg == "message".encode()

@patch("src.RP2040.time.sleep")
def test_readline_failure(mock_sleep, FakeSerial_fail):
        result = FakeSerial_fail.readline()
        assert result == "".encode()
        mock_sleep.assert_called_once_with(FakeSerial_fail.read_time * 0.25)

@patch("src.RP2040.random")
def test_readline_succeed(mock_random, FakeSerial_succeed):
    mock_random.return_value = 0
    FakeSerial_succeed.msg = "message".encode()
    assert FakeSerial_succeed.readline() == "message".encode()
    FakeSerial_succeed.msg = FakeSerial_succeed.hb_send_msg.encode()
    assert FakeSerial_succeed.readline() == FakeSerial_succeed.hb_receive_msg.encode()

# Testing with FakeSeiral_succeed as a natural default since it doesn't 
# branch over the success or failure case
def test_close_succeed(FakeSerial_succeed):
    FakeSerial_succeed.close()
