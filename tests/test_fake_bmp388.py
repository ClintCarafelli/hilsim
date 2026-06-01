"""Test the fake BMP388 sensor"""
from unittest.mock import patch

import pytest
from src.fake_bmp388 import FakeBMP388

# ------------------------------------------------------------------------------
# Setup
READINGS_LIST = [
    {"name": "pressure", "units": "hpa", "min": 300, "max": 1250},
    {"name": "air_temp", "units": "C", "min": 0, "max": 65},
]


@pytest.fixture
def success_config() -> dict:
    """Set up the basic config required"""
    return {"readings": READINGS_LIST, "failure_rate": 0}


# self.get_same_random is a surrogate for random() which is always less than 1,
#  which gurantees failure
@pytest.fixture
def failure_config() -> dict:
    """Set up a config that gurantees failure paths"""
    return {"readings": READINGS_LIST, "failure_rate": 1}


@pytest.fixture
def success_sensor(success_config: dict) -> FakeBMP388:
    """Create a sensor that successfully returns values"""
    return FakeBMP388(success_config)


@pytest.fixture
def fail_sensor(failure_config: dict) -> FakeBMP388:
    """Create a sensor that always fails"""
    return FakeBMP388(failure_config)


# ------------------------------------------------------------------------------
# Test _get_same_random() method

# Logic does not branch, but success_sensor.random should change every
# two readings


def test_get_same_random(success_sensor: FakeBMP388) -> None:
    """Ensure same random number is used for every 2 successive calls"""
    with patch("src.fake_bmp388.random", return_value=0.1):
        success_sensor._get_same_random()
        assert success_sensor.rand_num == 0.5
        assert success_sensor.counter == 1
        success_sensor._get_same_random()
        assert success_sensor.rand_num == 0.1
        assert success_sensor.counter == 2


# ------------------------------------------------------------------------------
# Test pressure property

# Two main branches:
#    - successful reading of the pressure property
#    - failed reading of the pressure property


def test_pressure_success(success_sensor: FakeBMP388) -> None:
    """Test a successful reading of the pressure property"""
    with patch("src.fake_bmp388.random", return_value=0.5):
        assert success_sensor.pressure == 775


def test_pressure_fail(fail_sensor: FakeBMP388) -> None:
    """Test a failed reading of the pressure property"""
    with pytest.raises(Exception):
        fail_sensor.pressure


# ------------------------------------------------------------------------------
# Test temperature property

# Two main branches:
#    - successful reading of the temperature property
#    - failed reading of the temperature property


def test_temperature_success(success_sensor: FakeBMP388) -> None:
    """Test a successful reading of the temperature property"""
    with patch("src.fake_bmp388.random", return_value=0.5):
        assert success_sensor.temperature == 32.5


def test_temperature_fail(fail_sensor: FakeBMP388) -> None:
    """Test a failed reading of the temperature property"""
    with pytest.raises(Exception):
        fail_sensor.temperature


# ------------------------------------------------------------------------------
