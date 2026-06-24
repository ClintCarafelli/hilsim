from unittest.mock import MagicMock, patch

import pytest
from hilsim.core.sensor_exceptions import UnknownVariableName
from hilsim.core.sensors import SensorBase

# ---------------------------------------------------------------------------------------
# Setup


@pytest.fixture
def world_state() -> MagicMock:
    """Create a fixture as world state that is really a MagicMock"""
    fake_world_state = MagicMock()
    fake_world_state.time.return_value = 0
    fake_world_state.state = {"variable_1": 17, "variable_2": 12, "time": 0}
    return fake_world_state


@pytest.fixture
def yield_sensor_base(sensor_config: dict, world_state: MagicMock):
    """Create instance of sensor base that does not run methods in __init__"""
    with patch.object(SensorBase, "_map_readings_to_name"):
        yield SensorBase(sensor_config["sensors"]["sensor_1"], world_state)


@pytest.fixture
def sensor_base(sensor_config: dict, world_state: MagicMock):
    """Create instance of sensor base"""
    return SensorBase(sensor_config["sensors"]["sensor_1"], world_state)


# ---------------------------------------------------------------------------------------
# Test instance construction

# No branches


def test_instance_construction(
    yield_sensor_base: SensorBase, sensor_config: dict
) -> None:
    """Test SensorBase instance construction"""
    ss_config = sensor_config["sensors"]["sensor_1"]
    assert yield_sensor_base.num_measurements == ss_config["num_measurements"]
    assert yield_sensor_base.readings_meta_data == ss_config["readings"]
    assert yield_sensor_base.failure_rate == ss_config["failure_rate"]
    assert hasattr(yield_sensor_base, "time")
    assert yield_sensor_base.counter == 0
    assert yield_sensor_base.rand_num == 0.0
    assert hasattr(yield_sensor_base, "world_state")
    assert hasattr(yield_sensor_base, "rmd_name_map")


# ---------------------------------------------------------------------------------------
# Test automatic registration with __init_subclass__

# No branches


def test_sensor_base_registers_subclass() -> None:
    """Make sure (imported) children are registered into SensorBase's registry"""

    class FakeSensor(SensorBase):
        pass

    assert "FakeSensor" in SensorBase.registry
    assert SensorBase.registry["FakeSensor"] is FakeSensor


# ---------------------------------------------------------------------------------------
# Test _map_readings_to_name() method:

# No branches


def test_map_readings_to_name(sensor_config: dict, sensor_base: SensorBase) -> None:
    """Test _map_readings_to_name method"""
    sensor_base._map_readings_to_name()
    assert sensor_base.rmd_name_map.keys() == {"variable_1", "variable_2"}
    assert (
        sensor_base.rmd_name_map["variable_1"]
        == sensor_config["sensors"]["sensor_1"]["readings"][0]
    )
    assert (
        sensor_base.rmd_name_map["variable_2"]
        == sensor_config["sensors"]["sensor_1"]["readings"][1]
    )


# ---------------------------------------------------------------------------------------
# Test _add_failure_possibility() method:

# Two branches:
#   - random is less than or equal to failure rate (fail!)
#   - random is greater than or equal to failure rate


def test_add_failure_possiblity_success(sensor_base: SensorBase) -> None:
    """Test add_failure_possiblity pass with success"""
    sensor_base.failure_rate = 0
    sensor_base.add_failure_possibility()


def test_add_failure_possiblity_fail(sensor_base: SensorBase) -> None:
    """Test add_failure_possiblity creates a failure (e.g. raises an exception)"""
    sensor_base.failure_rate = 1
    with pytest.raises(RuntimeError):
        sensor_base.add_failure_possibility()


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
    with patch("hilsim.core.sensors.random", side_effect=[0.1, 0.3]):
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
    var_name = "variable_1"
    sensor_base.rmd_name_map[var_name]["noise"] = 0.5
    sensor_base.rmd_name_map[var_name]["drift"] = 1
    sensor_base.time = 10
    with patch("hilsim.core.sensors.random", return_value=1):
        result = sensor_base._add_noise_and_drift(var_name)
        assert result == 10.5


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


def test_get_return_value_adding_noise_and_drift(
    sensor_base: SensorBase, world_state: MagicMock
) -> None:
    """Test get return value with adding noise and drift"""
    world_state.get.return_value = 17
    with patch.object(sensor_base, "_add_noise_and_drift", return_value=1) as mock_and:
        result = sensor_base.get_return_value("variable_1")
        assert result == 18
        mock_and.assert_called_once_with("variable_1")


def test_get_return_value_not_adding_noise_and_drift(
    sensor_base: SensorBase, world_state: MagicMock
) -> None:
    """Test get return value with adding noise and drift"""
    world_state.get.return_value = 17
    with patch.object(sensor_base, "_add_noise_and_drift", return_value=1) as mock_and:
        result = sensor_base.get_return_value("variable_1", False)
        assert result == 17
        mock_and.call_count == 0


def test_get_return_value_above_sensor_max(
    sensor_base: SensorBase, world_state: MagicMock
) -> None:
    """Test get return value with adding noise and drift"""
    world_state.get.return_value = 150
    result = sensor_base.get_return_value("variable_1", False)
    assert result == 100


def test_get_return_value_below_sensor_max(
    sensor_base: SensorBase, world_state: MagicMock
) -> None:
    """Test get return value with adding noise and drift"""
    world_state.get.return_value = -3
    result = sensor_base.get_return_value("variable_1", False)
    assert result == 0


# ---------------------------------------------------------------------------------------
