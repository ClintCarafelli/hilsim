"""Test the CommunicationInterface Class"""

import pytest
from src.controls import CommunicationInterface

# ---------------------------------------------------------------------------------------
# Setup
NOMINAL_CONFIG_DICT = {
    "sim": False,
    "super_sim": True,
    "super_sim_fr": 0,
    "baud_rate": 115200,
    "device_ID": "/dev/ttyACM0",
    "fake_device_ID": "/tmp/ttyVirtual1",
    "time_out": 1,
    "read_time": 0.5,
    "hb_send_msg": "ping",
    "hb_receive_msg": "pong",
}
DEVICE_NAME = "RP2040"


class MockClass(CommunicationInterface):
    """Build a mock class that inherits from CommunicationInterface"""

    def connect(self) -> bool:
        """must be included, enforced as an abstractmethod"""
        return True

    def disconnect(self):
        """must be included, enforced as an abstractmethod"""

    def read_and_write(self, send_msg: str, receive_msg: str) -> bool:
        """must be included, enforced as an abstractmethod"""
        return True


# ---------------------------------------------------------------------------------------
# Test instance construction
def test_init() -> None:
    """Test the inherited contruction from CommunicationInterface"""
    communicator = MockClass(NOMINAL_CONFIG_DICT, DEVICE_NAME)
    assert communicator.sim is False
    assert communicator.super_sim is True
    assert communicator.super_sim_fr == 0
    assert communicator.baud_rate == 115200
    assert communicator.device_id == "/dev/ttyACM0"
    assert communicator.fake_device_id == "/tmp/ttyVirtual1"
    assert communicator.time_out == 1
    assert communicator.read_time == 0.5
    assert communicator.hb_sm == "ping"
    assert communicator.hb_rm == "pong"
    assert communicator.pca is True
    assert communicator.connected is False
    assert communicator.device_name == DEVICE_NAME


# pylint: disable=abstract-class-instantiated


def test_is_abstract() -> None:
    """Ensure CommunicationInterface is Abstract (e.g. inherits from ABC)"""
    with pytest.raises(TypeError):
        CommunicationInterface(NOMINAL_CONFIG_DICT, DEVICE_NAME)  # type: ignore[abstract]


# ---------------------------------------------------------------------------------------
