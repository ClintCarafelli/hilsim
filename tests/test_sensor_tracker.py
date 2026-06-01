"""Test the sensor tracker"""

import operator
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from src.base_driver import Reading
from src.sensor_tracker import SensorTracker

# ---------------------------------------------------------------------------------------
# Setup
CONFIG_DICT = {
    "sensor_error_program": {
        "first_i2c_cycle": 4,
        "second_i2c_cycle": 5,
        "first_power_cycle": 6,
        "second_power_cycle": 7,
        "dead": 8,
    },
    "sensor_params": {"enabled_sensors": ["sensor1", "sensor2"]},
}

# Define some nominal (successful) results
SENSOR1_READING_1 = Reading("height", 10, "m")
SENSOR1_READING_2 = Reading("weight", 20, "kg")
SENSOR2_READING_1 = Reading("velocity", 2, "m/s")
SENSOR2_READING_2 = Reading("acceleration", -0.5, "m/s^2")
SENSOR_LIST_1 = [SENSOR1_READING_1, SENSOR1_READING_2]
SENSOR_LIST_2 = [SENSOR2_READING_1, SENSOR2_READING_2]
NOM_RESULTS = {"sensor1": SENSOR_LIST_1, "sensor2": SENSOR_LIST_2}

# Define some "failed readings (e.g. have a value of None)"
SENSOR1_READING_F1 = Reading("height", None, "m")
SENSOR1_READING_F2 = Reading("weight", None, "kg")
SENSOR_LIST_F1 = [SENSOR1_READING_F1, SENSOR1_READING_F2]
FAIL_RESULTS = {"sensor1": SENSOR_LIST_F1, "sensor2": SENSOR_LIST_2}


@pytest.fixture
def sensor_tracker() -> SensorTracker:
    """Create an instance of a sensor tracker"""
    return SensorTracker(CONFIG_DICT)


@pytest.fixture(autouse=True)
def mock_logger() -> Generator[MagicMock, None, None]:
    """Create a mock logger to be used throughout"""
    with patch("src.sensor_tracker.logger") as m:
        yield m


# ---------------------------------------------------------------------------------------
# Test the contructor behavior


def test_setup(sensor_tracker: SensorTracker) -> None:
    """test the contruction of the class instance"""
    # not testing the "get" on the enabled sensors because a lack thereof
    # would result in the whole system doing nothing (e.g. some sensors must be enabled)
    assert sensor_tracker.sensor_error_sol["i2c_cycle"] is False
    assert sensor_tracker.sensor_error_sol["power_cycle"] is False
    assert sensor_tracker.dead_sensors == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 0, "sensor2": 0}
    assert sensor_tracker.first_i2c_cycle_trig == 4
    assert sensor_tracker.second_i2c_cycle_trig == 5
    assert sensor_tracker.first_power_cycle_trig == 6
    assert sensor_tracker.second_power_cycle_trig == 7
    assert sensor_tracker.dead_trig == 8


# ---------------------------------------------------------------------------------------
# Test tracker() method:

# Four main parts of method:
#   - Finding Errors
#   - Determining cycling behavior
#   - Logging cycle triggers
#   - Declaring dead sensors
#
# Finding Errors (prior to dictonary subsets)
# Three branches:
#   - dead sensor
#   - no error on sensor and not dead
#   - error on sensor and not dead
#   - resetting error count upon nominal reading
#
# Power / Software cycles:
#   - either first or second i2c cycle is True
#   - both first or second i2c cycle is False
#   - either first or second power cycle is True
#   - both first or second power cycle is False
#
# Logging power/software cycle triggers:
#   - first_i2c_cycle is truthy
#   - first_i2c_cycle is not truthy
#   - second_i2c_cycle is truthy
#   - second_i2c_cycle is not truthy
#   - first_power_cycle is truthy
#   - first_power_cycle is not truthy
#   - second_power_cycle is truthy
#   - second_power_cycle is not truthy
#
# Declare dead sensors:
#   - there are sensors to declare dead
#   - there are no sensors to declare dead


def test_track_nom_readings(sensor_tracker: SensorTracker) -> None:
    """Test nominal (good) reading input to tracker"""
    results = sensor_tracker.track(NOM_RESULTS)
    assert results == {"i2c_cycle": False, "power_cycle": False}
    assert sensor_tracker.dead_sensors == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 0, "sensor2": 0}


def test_track_failed_readings_transient(
    mock_logger: Generator[MagicMock, None, None], sensor_tracker: SensorTracker
) -> None:
    """Test failed readings before any cycling"""
    results = sensor_tracker.track(FAIL_RESULTS)
    assert results == {"i2c_cycle": False, "power_cycle": False}
    assert sensor_tracker.dead_sensors == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 1, "sensor2": 0}
    mock_logger.error.assert_called()

    results = sensor_tracker.track(FAIL_RESULTS)
    assert results == {"i2c_cycle": False, "power_cycle": False}
    assert sensor_tracker.dead_sensors == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 2, "sensor2": 0}
    mock_logger.error.assert_called()

    results = sensor_tracker.track(FAIL_RESULTS)
    assert results == {"i2c_cycle": False, "power_cycle": False}
    assert sensor_tracker.dead_sensors == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 3, "sensor2": 0}
    mock_logger.error.assert_called()


def test_track_failed_readings_software_cycle(
    mock_logger: Generator[MagicMock, None, None], sensor_tracker: SensorTracker
) -> None:
    """Test failed readings triggering software cycles"""
    sensor_tracker.sensor_errors = {"sensor1": 3, "sensor2": 0}
    results = sensor_tracker.track(FAIL_RESULTS)
    assert results == {"i2c_cycle": True, "power_cycle": False}
    assert sensor_tracker.dead_sensors == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 4, "sensor2": 0}
    mock_logger.error.assert_called()
    mock_logger.info.assert_called()

    results = sensor_tracker.track(FAIL_RESULTS)
    assert results == {"i2c_cycle": True, "power_cycle": False}
    assert sensor_tracker.dead_sensors == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 5, "sensor2": 0}
    mock_logger.error.assert_called()
    mock_logger.info.assert_called()


def test_track_failed_readings_power_cycle(
    mock_logger: Generator[MagicMock, None, None], sensor_tracker: SensorTracker
) -> None:
    """Test failed readings triggering power cycles"""
    sensor_tracker.sensor_errors = {"sensor1": 5, "sensor2": 0}
    results = sensor_tracker.track(FAIL_RESULTS)
    assert results == {"i2c_cycle": False, "power_cycle": True}
    assert sensor_tracker.dead_sensors == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 6, "sensor2": 0}
    mock_logger.error.assert_called()
    mock_logger.info.assert_called()

    results = sensor_tracker.track(FAIL_RESULTS)
    assert results == {"i2c_cycle": False, "power_cycle": True}
    assert sensor_tracker.dead_sensors == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 7, "sensor2": 0}
    mock_logger.error.assert_called()
    mock_logger.info.assert_called()


def test_track_dead_sensor_decleration(
    mock_logger: Generator[MagicMock, None, None], sensor_tracker: SensorTracker
) -> None:
    """Test dead sensor declaration"""
    sensor_tracker.sensor_errors = {"sensor1": 7, "sensor2": 0}
    results = sensor_tracker.track(FAIL_RESULTS)
    assert sensor_tracker.sensor_errors == {"sensor1": 0, "sensor2": 0}
    assert results == {"i2c_cycle": False, "power_cycle": False}
    assert sensor_tracker.dead_sensors == {"sensor1": True, "sensor2": False}
    mock_logger.error.assert_called()
    mock_logger.critical.assert_called()


def test_track_dead_sensor_no_mitigation(sensor_tracker: SensorTracker) -> None:
    """Test dead sensor among nominal readings"""
    sensor_tracker.dead_sensors = {"sensor1": True, "sensor2": False}
    results = sensor_tracker.track(FAIL_RESULTS)
    assert results == {"i2c_cycle": False, "power_cycle": False}
    assert sensor_tracker.dead_sensors == {"sensor1": True, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 0, "sensor2": 0}


def test_track_reset_error_count(sensor_tracker: SensorTracker) -> None:
    """Test resetting error count upon nominal reading"""
    sensor_tracker.sensor_errors = {"sensor1": 2, "sensor2": 5}
    results = sensor_tracker.track(NOM_RESULTS)
    assert sensor_tracker.sensor_errors == {"sensor1": 0, "sensor2": 0}
    assert results == {"i2c_cycle": False, "power_cycle": False}
    assert sensor_tracker.dead_sensors == {"sensor1": False, "sensor2": False}


# ---------------------------------------------------------------------------------------
# Test _dictonary_subset() method:
d = {"item1": 1, "item2": 2, "item3": 3}


def test_dictonary_subset(sensor_tracker: SensorTracker) -> None:
    """Test dictonary subset method"""
    assert sensor_tracker._dictonary_subset(d, 2, operator.eq) == {"item2": 2}
    assert sensor_tracker._dictonary_subset(d, 2, operator.lt) == {"item1": 1}
    assert sensor_tracker._dictonary_subset(d, 2, operator.le) == {
        "item1": 1,
        "item2": 2,
    }
    assert sensor_tracker._dictonary_subset(d, 2, operator.gt) == {"item3": 3}
    assert sensor_tracker._dictonary_subset(d, 2, operator.gt) == {"item3": 3}
    assert sensor_tracker._dictonary_subset(d, 2, operator.ge) == {
        "item2": 2,
        "item3": 3,
    }
    assert sensor_tracker._dictonary_subset(d, 2, operator.ne) == {
        "item1": 1,
        "item3": 3,
    }


# ---------------------------------------------------------------------------------------
