"""Test the fake_stemma sensor"""

from unittest.mock import patch, MagicMock

import pytest
from src.stemma import FakeSTEMMA

# ------------------------------------------------------------------------------
# Setup
WORLD_STATE = MagicMock()
READINGS_LIST = [
    {"name": "moisture", "units": "None", "max": 2000, "min": 200},
    {"name": "temp", "units": "C", "max": 85, "min": -40},
]


@pytest.fixture
def config() -> dict:
    """Create a basic config for the fake_stemma"""
    return {"readings": READINGS_LIST, "failure_rate": 0, "num_measurements": 2}


@pytest.fixture
def fake_sensor(config: dict) -> FakeSTEMMA:
    """Create an instance of a FakeSTEMMA"""
    return FakeSTEMMA(config, WORLD_STATE)


# ------------------------------------------------------------------------------
# Test moisture_read() method

# No branches, failure handled in base class


def test_moisture_read(fake_sensor: FakeSTEMMA) -> None:
    """test a successful moisture value read"""
    with (
        patch.object(fake_sensor, "add_failure_possibility") as afp,
        patch.object(fake_sensor, "get_return_value", return_value=21) as grv,
    ):
        assert fake_sensor.moisture_read() == 21
        afp.assert_called_once()
        grv.assert_called_once()



# ------------------------------------------------------------------------------
# Test get_temp() method

# No branches, failure handled in base class

def test_temp_read_success(fake_sensor: FakeSTEMMA) -> None:
    """Test a successful reading of the chip temperature"""
    with (
        patch.object(fake_sensor, "add_failure_possibility") as afp,
        patch.object(fake_sensor, "get_return_value", return_value=19) as grv,
    ):
        assert fake_sensor.get_temp() == 19
        afp.assert_called_once()
        grv.assert_called_once()

# ------------------------------------------------------------------------------
