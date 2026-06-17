"""Test the SensorBase class"""

from unittest.mock import MagicMock, patch

import pytest
from src.base_driver import SensorBase
from src.sensor_exceptions import UnknownVariableName

# ---------------------------------------------------------------------------------------
# Setup

CONFIG_DICT = {
    "description": "reads param_1 and param_2",
    "num_measurements": "2",
    "i2c_address": 0x36,
    "driver": "Sensor1Driver",
    "sim": True,
    "failure_rate": 0,
    "sim_failure_initialization": False,
    "readings": [
        {"name": "param_1", "max": 20, "min": 10, "noise": 0.5, "drift": 0.5},
        {"name": "param_2", "max": 30, "min": 15, "noise": 0.5, "drift": 0},
    ],
}

WORLD_STATE = MagicMock()
WORLD_STATE.time.return_value = 0
WORLD_STATE.state = {"param_1": 17, "param_2": 12}


@pytest.fixture
def sensor_base_w_yield():
    """Create an instance of the sensor base class with patched method calls in construction"""
    with patch.object(SensorBase, "_map_readings_to_noise"):
        yield SensorBase(CONFIG_DICT, WORLD_STATE)


@pytest.fixture
def sensor_base() -> SensorBase:
    """Create an instance of the sensor base class"""
    return SensorBase(CONFIG_DICT, WORLD_STATE)


# ---------------------------------------------------------------------------------------
# Test instance construction


def test_instance_construction(sensor_base_w_yield: SensorBase) -> None:
    """Test the construction of an instance of SensorBase"""
    assert sensor_base_w_yield.counter == 0
    assert sensor_base_w_yield.rand_num == 0
    assert sensor_base_w_yield.world_state == WORLD_STATE
    assert hasattr(sensor_base_w_yield, "num_measurements")
    assert hasattr(sensor_base_w_yield, "readings_meta_data")
    assert hasattr(sensor_base_w_yield, "failure_rate")
    assert hasattr(sensor_base_w_yield, "time")
    assert hasattr(sensor_base_w_yield, "rmd_name_map")
    sensor_base_w_yield._map_readings_to_noise.assert_called_once()


# ---------------------------------------------------------------------------------------
# Test _map_readings_to_noise_method()

# No branches:

# Note: don't actually have to call the method because it is called during
# instance construction


def test_map_readings_to_noise(sensor_base: SensorBase) -> None:
    """Test the map_readings_to_noise method"""
    should_be_keys = {"param_1", "param_2"}
    # print(sensor_base.readings_meta_data)
    assert should_be_keys <= sensor_base.rmd_name_map.keys()
    assert len(sensor_base.rmd_name_map.keys()) == 2
    assert sensor_base.rmd_name_map["param_1"] == {
        "name": "param_1",
        "max": 20,
        "min": 10,
        "noise": 0.5,
        "drift": 0.5,
    }
    assert sensor_base.rmd_name_map["param_2"] == {
        "name": "param_2",
        "max": 30,
        "min": 15,
        "noise": 0.5,
        "drift": 0,
    }


# ---------------------------------------------------------------------------------------
# Test _add_failure_possibility() method:

# Two branches:
#    - Raises RuntimeError
#    - return


def test_add_failure_possibility_failure(sensor_base: SensorBase) -> None:
    """Test the _add_failure_possibility creating a failure by raising an exception"""
    sensor_base.failure_rate = 1
    with pytest.raises(RuntimeError):
        sensor_base.add_failure_possibility()


def test_add_failure_possibility(sensor_base: SensorBase) -> None:
    """Test the _add_failure_possibility that does not create a failure"""
    sensor_base.failure_rate = 0
    result = sensor_base.add_failure_possibility()
    assert result is None


# ---------------------------------------------------------------------------------------
# Test _get_same_random() method:

# Returns same random every three calls, two main branches:
#   - if counter % 2 is zero (divisible by two, create new random number and save it)
#   - if counter is not dvisible by two, than return the saved random number
#   - note the counter should increment after every call to the method

# note that _get_same_random() derives when to change the random number from the
# number of measurements that the sensor creates


def test_get_same_random(sensor_base: SensorBase) -> None:
    """Test the get same random method: make sure it returns same number when
    called two times in a row, and a new number on the 4th"""
    with patch("src.base_driver.random", side_effect=[0.1, 0.3]):
        sensor_base._get_same_random()
        assert sensor_base.rand_num == 0.1
        assert sensor_base.counter == 1
        sensor_base._get_same_random()
        assert sensor_base.rand_num == 0.1
        assert sensor_base.counter == 2
        sensor_base._get_same_random()
        assert sensor_base.rand_num == 0.3
        assert sensor_base.counter == 3


# ---------------------------------------------------------------------------------------
# Test _add_noise_and_drift() method:

# No branches


def test_add_noise_and_drift(sensor_base: SensorBase) -> None:
    """Test the _add_noise_and_drift() method"""
    sensor_base.time = 10
    with patch("src.base_driver.random", return_value=0.3):
        result = sensor_base._add_noise_and_drift("param_1")
        assert result == 4.8


# ---------------------------------------------------------------------------------------
# Test get_return_value() method:

# Branches:
#   - Unknown variable name
#   - If adding noise and drift:
#   - if not adding noise and drift
#   - dynamics value above sensor max
#   - dynamics value below sensor min
#   - dynamics value inbetween sensor max and sensor min


def test_get_return_value_unknown_var(sensor_base: SensorBase) -> None:
    """Test get return value raising an unknown variable error"""
    with pytest.raises(UnknownVariableName):
        sensor_base.get_return_value("not_a_variable")


def test_get_return_value_adding_noise_and_drift(sensor_base: SensorBase) -> None:
    """Test get return value with adding noise and drift"""
    WORLD_STATE.get.return_value = 17
    with patch.object(sensor_base, "_add_noise_and_drift", return_value=1) as mock_and:
        result = sensor_base.get_return_value("param_1")
        assert result == 18
        mock_and.assert_called_once_with("param_1")


def test_get_return_value_not_adding_noise_and_drift(sensor_base: SensorBase) -> None:
    """Test get return value with adding noise and drift"""
    WORLD_STATE.get.return_value = 17
    with patch.object(sensor_base, "_add_noise_and_drift", return_value=1) as mock_and:
        result = sensor_base.get_return_value("param_1", False)
        assert result == 17
        mock_and.call_count == 0


def test_get_return_value_above_sensor_max(sensor_base: SensorBase) -> None:
    """Test get return value with adding noise and drift"""
    WORLD_STATE.get.return_value = 5000
    result = sensor_base.get_return_value("param_1", False)
    assert result == 20


def test_get_return_value_below_sensor_max(sensor_base: SensorBase) -> None:
    """Test get return value with adding noise and drift"""
    WORLD_STATE.get.return_value = 0
    result = sensor_base.get_return_value("param_1", False)
    assert result == 10


# ---------------------------------------------------------------------------------------
