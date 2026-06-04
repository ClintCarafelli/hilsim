"""Test the fake_stemma sensor"""

from unittest.mock import patch

import pytest
from src.stemma import FakeSTEMMA

# ------------------------------------------------------------------------------
# Setup
READINGS_LIST = [
    {"name": "moisture", "units": "None", "max": 2000, "min": 200},
    {"name": "temp", "units": "C", "max": 85, "min": -40},
]


@pytest.fixture
def config() -> dict:
    """Create a basic config for the fake_stemma"""
    return {"readings": READINGS_LIST, "failure_rate": 0}


@pytest.fixture
def fake_sensor(config: dict) -> FakeSTEMMA:
    """Create an instance of a FakeSTEMMA"""
    return FakeSTEMMA(config)


# ------------------------------------------------------------------------------
# Test moisture_read() method

# Two branches:
#   - successful reading
#   - failed reading


def test_moisture_read_success(fake_sensor: FakeSTEMMA) -> None:
    """test a successful moisture value read"""
    with patch.object(fake_sensor, "_in_range", return_value=10):
        result = fake_sensor.moisture_read()
        assert result == 10


def test_moisture_read_fail(fake_sensor: FakeSTEMMA) -> None:
    """test a failed moisture value read"""
    fake_sensor.failure_rate = 1
    with pytest.raises(Exception):
        fake_sensor.moisture_read()


# ------------------------------------------------------------------------------
# Test get_temp() method

# Two branches:
#   - successful reading
#   - failed reading


def test_temp_read_success(fake_sensor: FakeSTEMMA) -> None:
    """Test a successful reading of the chip temperature"""
    with patch.object(fake_sensor, "_in_range", return_value=9):
        result = fake_sensor.get_temp()
        assert result == 9


def test_temp_read_fail(fake_sensor: FakeSTEMMA) -> None:
    """Test a failed reading of the chip temperature"""
    fake_sensor.failure_rate = 1
    with pytest.raises(Exception):
        fake_sensor.get_temp()


# ------------------------------------------------------------------------------
# Test _in_range() method

# No branches, but three cases, if random() = 1, then should return max,
# if random() = 0, then should return min, added case in middle too


def test_in_range(fake_sensor):
    """Test the _in_rnage method (three cases)"""
    with patch("src.stemma.random", return_value=0.0):
        result = fake_sensor._in_range("moisture")
        assert result == 200.0
    with patch("src.stemma.random", return_value=0.5):
        result = fake_sensor._in_range("moisture")
        assert result == 1100.0
    with patch("src.stemma.random", return_value=1):
        result = fake_sensor._in_range("moisture")
        assert result == 2000.0


# ------------------------------------------------------------------------------
# Test _get_same_random() method

# No branches, but self.random should change every two calls to the method


def test_get_same_random(fake_sensor):
    """Test the get same random (self.random new value every two calls)"""
    with patch("src.stemma.random", return_value=0.1):
        fake_sensor._get_same_random()
        assert fake_sensor.rand_num == 0
        assert fake_sensor.counter == 1
        fake_sensor._get_same_random()
        assert fake_sensor.rand_num == 0.1
        assert fake_sensor.counter == 2


# ------------------------------------------------------------------------------
