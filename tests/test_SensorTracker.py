import pytest
import operator
from unittest.mock import patch, MagicMock
from src.SensorTracker import SensorTracker
from src.BaseSensor import Reading


config_dict = {"sensor_error_program":
                {"first_i2c_cycle": 4,
                 "second_i2c_cycle": 5,
                 "first_power_cycle": 6,
                 "second_power_cycle": 7,
                 "dead": 8},
                 "sensor_params": 
                 {"enabled_sensors":
                 ["sensor1", "sensor2"]}}

sensor1_reading_1 = Reading("height", 10, "m")
sensor1_reading_2 = Reading("weight", 20, "kg") 
sensor2_reading_1 = Reading("velocity", 2, "m/s")
sensor2_reading_2 = Reading("acceleration", -0.5, "m/s^2") 
sensor_list_1 = [sensor1_reading_1, sensor1_reading_2]
sensor_list_2 = [sensor2_reading_1, sensor2_reading_2]
nom_results = {"sensor1": sensor_list_1, "sensor2": sensor_list_2}

sensor1_reading_f1 = Reading("height", None, "m")
sensor1_reading_f2 = Reading("weight", None, "kg")
sensor_list_f1 = [sensor1_reading_f1, sensor1_reading_f2]
fail_results =  {"sensor1": sensor_list_f1, "sensor2": sensor_list_2}


@pytest.fixture
def sensor_tracker():
    return SensorTracker(config_dict)

@pytest.fixture(autouse=True) 
def mock_logger():
    with patch('src.SensorTracker.logger') as m:
        yield m

def test_setup(sensor_tracker): 
    # not testing the "get" on the enabled sensors because a lack thereof 
    # would result in the whole system doing nothing (e.g. some sensors must be enabled)
    assert sensor_tracker.sensor_error_sol["i2c_cycle"] is False
    assert sensor_tracker.sensor_error_sol["power_cycle"] is False
    assert sensor_tracker.dead_sensors  == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 0, "sensor2": 0}
    assert sensor_tracker.first_i2c_cycle_trig    == 4
    assert sensor_tracker.second_i2c_cycle_trig   == 5
    assert sensor_tracker.first_power_cycle_trig  == 6
    assert sensor_tracker.second_power_cycle_trig == 7
    assert sensor_tracker.dead_trig               == 8

def test_track_nom_readings(sensor_tracker): 
    results =  sensor_tracker.track(nom_results)
    assert results == {"i2c_cycle": False, "power_cycle": False}
    assert sensor_tracker.dead_sensors  == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 0, "sensor2": 0}

def test_track_failed_readings_transient(mock_logger, sensor_tracker):
    results = sensor_tracker.track(fail_results)
    assert results == {"i2c_cycle": False, "power_cycle": False}
    assert sensor_tracker.dead_sensors  == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 1, "sensor2": 0}
    mock_logger.error.assert_called_with("Error detected on 'sensor1': reading was 'height' with 'None m'")

    results = sensor_tracker.track(fail_results)
    assert results == {"i2c_cycle": False, "power_cycle": False}
    assert sensor_tracker.dead_sensors  == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 2, "sensor2": 0}
    mock_logger.error.assert_called_with("Error detected on 'sensor1': reading was 'height' with 'None m'")

    results = sensor_tracker.track(fail_results)
    assert results == {"i2c_cycle": False, "power_cycle": False}
    assert sensor_tracker.dead_sensors  == {"sensor1": False, "sensor2": False}
    assert sensor_tracker.sensor_errors == {"sensor1": 3, "sensor2": 0}
    mock_logger.error.assert_called_with("Error detected on 'sensor1': reading was 'height' with 'None m'")

def test_track_failed_readings_software_cycle(mock_logger, sensor_tracker):
        sensor_tracker.sensor_errors = {"sensor1": 3, "sensor2": 0}
        results = sensor_tracker.track(fail_results)
        assert results == {"i2c_cycle": True, "power_cycle": False}
        assert sensor_tracker.dead_sensors  == {"sensor1": False, "sensor2": False}
        assert sensor_tracker.sensor_errors == {"sensor1": 4, "sensor2": 0}
        mock_logger.error.assert_called_with("Error detected on 'sensor1': reading was 'height' with 'None m'")
        mock_logger.info.assert_called_with("sensor1 caused a first instance of an i2c bus cycle")

        results = sensor_tracker.track(fail_results)
        assert results == {"i2c_cycle": True, "power_cycle": False}
        assert sensor_tracker.dead_sensors  == {"sensor1": False, "sensor2": False}
        assert sensor_tracker.sensor_errors == {"sensor1": 5, "sensor2": 0}
        mock_logger.error.assert_called_with("Error detected on 'sensor1': reading was 'height' with 'None m'")
        mock_logger.info.assert_called_with("sensor1 caused a second instance of an i2c bus cycle")

def test_track_failed_readings_power_cycle(mock_logger, sensor_tracker):
        sensor_tracker.sensor_errors = {"sensor1": 5, "sensor2": 0}
        results = sensor_tracker.track(fail_results)
        assert results == {"i2c_cycle": False, "power_cycle": True}
        assert sensor_tracker.dead_sensors  == {"sensor1": False, "sensor2": False}
        assert sensor_tracker.sensor_errors == {"sensor1": 6, "sensor2": 0}
        mock_logger.error.assert_called_with("Error detected on 'sensor1': reading was 'height' with 'None m'")
        mock_logger.info.assert_called_with("sensor1 caused a first instance of a sensor suite power cycle (if available)")

        results = sensor_tracker.track(fail_results)
        assert results == {"i2c_cycle": False, "power_cycle": True}
        assert sensor_tracker.dead_sensors  == {"sensor1": False, "sensor2": False}
        assert sensor_tracker.sensor_errors == {"sensor1": 7, "sensor2": 0}
        mock_logger.error.assert_called_with("Error detected on 'sensor1': reading was 'height' with 'None m'")
        mock_logger.info.assert_called_with("sensor1 caused a second instance of a sensor suite power cycle (if available)")

def test_track_dead_sensor_decleration(mock_logger, sensor_tracker):
        sensor_tracker.sensor_errors = {"sensor1": 7, "sensor2": 0}
        results = sensor_tracker.track(fail_results)
        assert sensor_tracker.sensor_errors == {"sensor1": 0, "sensor2": 0}
        assert results == {"i2c_cycle": False, "power_cycle": False}
        assert sensor_tracker.dead_sensors == {"sensor1": True, "sensor2": False}
        mock_logger.error.assert_called_with("Error detected on 'sensor1': reading was 'height' with 'None m'")
        mock_logger.critical("sensor1 declared dead. No further recovery measures for sensor1")

def test_track_dead_sensor_no_mitigation(mock_logger, sensor_tracker): 
       sensor_tracker.dead_sensors = {"sensor1": True, "sensor2": False}
       results = sensor_tracker.track(fail_results)
       assert results == {"i2c_cycle": False, "power_cycle": False}
       assert sensor_tracker.dead_sensors ==  {"sensor1": True, "sensor2": False}
       assert sensor_tracker.sensor_errors == {"sensor1": 0, "sensor2": 0}

def test_track_reset_error_count(sensor_tracker):
    sensor_tracker.sensor_errors = {"sensor1": 2, "sensor2": 5}
    results = sensor_tracker.track(nom_results)
    assert sensor_tracker.sensor_errors == {"sensor1": 0, "sensor2": 0}
    assert results == {"i2c_cycle": False, "power_cycle": False}
    assert sensor_tracker.dead_sensors == {"sensor1": False, "sensor2": False}

d = {"item1": 1, "item2": 2, "item3": 3}

def test_dictonary_subset_eq(sensor_tracker):
    assert sensor_tracker._dictonary_subset(d, 2, operator.eq) == {"item2": 2}
    assert sensor_tracker._dictonary_subset(d, 2, operator.lt) == {"item1": 1}
    assert sensor_tracker._dictonary_subset(d, 2, operator.le) == {"item1": 1, "item2": 2}
    assert sensor_tracker._dictonary_subset(d, 2, operator.gt) == {"item3": 3}
    assert sensor_tracker._dictonary_subset(d, 2, operator.gt) ==  {"item3": 3}
    assert sensor_tracker._dictonary_subset(d, 2, operator.ge) == {"item2": 2, "item3": 3}
    assert sensor_tracker._dictonary_subset(d, 2, operator.ne) == {"item1": 1, "item3": 3}
     
     










      






