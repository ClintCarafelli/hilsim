"""Test the fake BMP388 sensor"""

from unittest.mock import patch, MagicMock

import pytest
from src.bmp388 import FakeBMP388

# ------------------------------------------------------------------------------
# Setup
READINGS_LIST = [
    {"name": "pressure", "units": "hpa", "min": 300, "max": 1250},
    {"name": "air_temp", "units": "C", "min": 0, "max": 65},
]
WORLD_STATE = MagicMock()


@pytest.fixture
def success_config() -> dict:
    """Set up the basic config required"""
    return {"readings": READINGS_LIST, "failure_rate": 0, "num_measurements": 2}


# self.get_same_random is a surrogate for random() which is always less than 1,
#  which gurantees failure
@pytest.fixture
def failure_config() -> dict:
    """Set up a config that gurantees failure paths"""
    return {"readings": READINGS_LIST, "failure_rate": 1, "num_measurements": 2}


@pytest.fixture
def success_sensor(success_config: dict) -> FakeBMP388:
    """Create a sensor that successfully returns values"""
    return FakeBMP388(success_config, WORLD_STATE)


# ------------------------------------------------------------------------------
# Test pressure property

# No branches, failures are handled in base class SensorBase


def test_pressure(success_sensor: FakeBMP388) -> None:
    """Test a successful reading of the pressure property"""
    with (
        patch.object(success_sensor, "add_failure_possibility") as afp,
        patch.object(success_sensor, "get_return_value", return_value=223) as grv,
    ):
        assert success_sensor.pressure == 223
        afp.assert_called_once()
        grv.assert_called_once()


# ------------------------------------------------------------------------------
# Test temperature property

# No branches, failures are handled in base class SensorBase


def test_temperature(success_sensor: FakeBMP388) -> None:
    """Test a successful reading of the temperature property"""
    with (
        patch.object(success_sensor, "add_failure_possibility") as afp,
        patch.object(success_sensor, "get_return_value", return_value=223) as grv,
    ):
        assert success_sensor.temperature == 223
        afp.assert_called_once()
        grv.assert_called_once()


# ------------------------------------------------------------------------------
