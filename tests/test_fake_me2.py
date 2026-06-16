""" Test the fake_me2 sensor that does not require hardware"""

from unittest.mock import patch, MagicMock
import pytest
from src.me2 import FakeME2


# ------------------------------------------------------------------------------
# Setup
READINGS_LIST = [{"name": "oxygen", "units": "percent", "min": 0, "max": 25}]
WORLD_STATE = MagicMock()

@pytest.fixture
def config() -> dict:
    """create config dict that does not fail"""
    return {"readings": READINGS_LIST, "failure_rate": 0, "num_measurements": 1}

@pytest.fixture
def fake_sensor(config: dict) -> FakeME2: 
    return FakeME2(config, WORLD_STATE)

# ------------------------------------------------------------------------------
# Test get_oxygen_data() method

# No branches, failure handled in base class SensorBase

def test_get_oxygen_data(fake_sensor: dict) -> None:
    """Test failed value production"""
    with (
        patch.object(fake_sensor, "add_failure_possibility") as afp,
        patch.object(fake_sensor, "get_return_value", return_value=223) as grv,
    ):
        assert fake_sensor.get_oxygen_data(10) == 223
        afp.assert_called_once()
        grv.assert_called_once()


# ------------------------------------------------------------------------------