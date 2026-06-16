"""Test the FakeINA260 class"""

from unittest.mock import patch, MagicMock
import pytest
from src.ina260 import FakeINA260


# ---------------------------------------------------------------------------------------
# Setup
WORLD_STATE = MagicMock()

@pytest.fixture
def base_config() -> dict:
    "build the base configuration used for testing"
    return {
        "failure_rate": 0,
        "num_measurements": 3,
        "readings": [{"name": "current", "noise": 0.5}, 
                    {"name": "voltage", "noise": 0.5},
                    {"name": "power", "noise": 0.5}]
    }


@pytest.fixture
def off_status() -> dict:
    "create off status dictonary"
    return {"obj_1": "off", "obj_2": "off"}


@pytest.fixture
def on_status() -> dict:
    """create on status dictonary"""
    return {"obj_1": "on", "obj_2": "on"}


@pytest.fixture
def fake_sensor(base_config: dict) -> FakeINA260:
    """Return instance of FakeINA260 with the base configuration"""
    return FakeINA260(base_config, WORLD_STATE)


# ---------------------------------------------------------------------------------------
# test voltage() property

# No branches, any branching is handled in the parent class SensorBase

def test_voltage(fake_sensor: FakeINA260) -> None:
    """Test the successful voltage reading branch"""
    with (patch.object(fake_sensor, "add_failure_possibility", return_value=0) as afp,
    patch.object(fake_sensor, "get_return_value", return_value=12) as grv):
            result = fake_sensor.voltage
            assert result == 12
            afp.assert_called_once()
            grv.assert_called_once()


# ---------------------------------------------------------------------------------------
# test current() property

# Two branches:
#   - successful value generation
#   - failed value generation


def test_current(fake_sensor: FakeINA260) -> None:
    """Test a successful current reading"""
    WORLD_STATE.get.return_value = 100
    with (patch.object(fake_sensor, "add_failure_possibility") as afp,
        patch.object(fake_sensor, "get_return_value", return_value=100.5) as grv):
        result = fake_sensor.current
        assert result == 100.5
        afp.assert_called_once()
        grv.assert_called_once()


# ---------------------------------------------------------------------------------------
# test power() property

# Two branches:
#   - successful value generation
#   - failed value generation based on failure rate


def test_power_success(fake_sensor: FakeINA260) -> None:
    """test a successful reading of the power property"""
    with patch.object(fake_sensor, "add_failure_possibility"):
        fake_sensor.current_val = 10
        fake_sensor.voltage_val = 12.8
        result = fake_sensor.power
        assert result == 128

# ---------------------------------------------------------------------------------------