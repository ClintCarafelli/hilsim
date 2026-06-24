import pytest


"""Test the CommunicationInterface Class"""

import pytest
from src.hilsim.core.controls import CommunicationInterface

# ---------------------------------------------------------------------------------------
# Setup

@pytest.fixture
def config(device_config: dict) -> dict:
    """Query the dictonary of the single device"""
    return device_config["devices"]["device_1"]

@pytest.fixture
def device_name() -> str: 
    """Query the device name of the device 1"""
    return "device_1"


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
def test_init(config: dict, device_name: str) -> None:
    """Test the inherited contruction from CommunicationInterface"""
    communicator = MockClass(config, device_name)
    assert communicator.sim is config["sim"]
    assert communicator.super_sim is config["super_sim"]
    assert communicator.super_sim_fr == config["super_sim_fr"]
    assert communicator.baud_rate == config["baud_rate"]
    assert communicator.device_id == config["device_ID"]
    assert communicator.fake_device_id == config["fake_device_ID"]
    assert communicator.time_out == config["time_out"]
    assert communicator.read_time == config["read_time"]
    assert communicator.hb_sm == config["hb_send_msg"]
    assert communicator.hb_rm == config["hb_receive_msg"]
    assert communicator.connected is False
    assert communicator.device_name == device_name


# pylint: disable=abstract-class-instantiated


def test_is_abstract(config: dict, device_name: str) -> None:
    """Ensure CommunicationInterface is Abstract (e.g. inherits from ABC)"""
    with pytest.raises(TypeError):
        CommunicationInterface(config, device_name)  # type: ignore[abstract]


# ---------------------------------------------------------------------------------------
