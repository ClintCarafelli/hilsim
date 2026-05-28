import pytest 
from unittest.mock import patch, MagicMock
from src.SensorManager import SensorManager
from src.SensorExceptions import SensorInitError, SensorReadError, ConfigError
import copy
from src.BaseSensor import Reading

#------------------------------------------------------------------------------
#Setup

i2c_bus = MagicMock()
config_dict = {"sensor_params": {"enabled_sensors": 
                                 ["sensor_1", "sensor_2"],
                                 "sim_all": True}, 
                "sensors": {"sensor_1": {"description": "fake sensor 1, " + 
                                        "reads speed",
                                        "sensor_num": 1,
                                        "num_measurements": 1,
                                        "driver": "sensor_1_driver",
                                        "sim": True,
                                        "failure_rate": 0},
                            "sensor_2": {"description": "fake sensor 2, " + 
                                        "reads weight and temperature",
                                        "sensor_num": 1,
                                        "num_measurements": 2,
                                        "driver": "sensor_2_driver",
                                        "sim": False,
                                        "failure_rate": 0}}}
@pytest.fixture
def base_config():
    return config_dict

@pytest.fixture
def no_enabled_sensors_config(base_config):
    copy_config = copy.deepcopy(base_config)
    copy_config["sensor_params"]["enabled_sensors"] = []
    return copy_config

@pytest.fixture
def missing_meta_data_config(base_config):
    copy_config = copy.deepcopy(base_config)
    copy_config["sensors"] = {"sensor_1":{"description": "fake sensor 1, reads speed",
                                        "sensor_num": 1,
                                        "sensor_num_measurements": 1,
                                        "driver": "sensor_1_driver",
                                        "sim": True,
                                        "failure_rate": 0}}
    return copy_config

@pytest.fixture
def missing_driver_field_config(base_config):
    copy_config = copy.deepcopy(base_config)
    copy_config["sensors"]["sensor_1"].__delitem__("driver")
    return copy_config

@pytest.fixture
def empty_driver_field_config(base_config):
    copy_config = copy.deepcopy(base_config)
    copy_config["sensors"]["sensor_1"]["driver"] = None
    return copy_config

@pytest.fixture
def wrong_driver_name_config(base_config):
    copy_config = copy.deepcopy(base_config)
    copy_config["sensors"]["sensor_1"]["driver"] = "not_a_driver"
    return copy_config

@pytest.fixture
def mock_driver_registry():
    mock_driver_1 = MagicMock()
    mock_driver_1.__name__ = "MockSensor1Driver"
    mock_driver_2 = MagicMock()
    mock_driver_2.__name__ = "MockSensor2Driver"
    mock_registry = {
        "sensor_1_driver": mock_driver_1,
        "sensor_2_driver": mock_driver_2,
    }
    return mock_registry

@pytest.fixture
def mock_fake_sensor_registry():
    mock_fake_sensor_1 = MagicMock()
    mock_fake_sensor_2 = MagicMock()
    mock_registry = {
        "sensor_1": mock_fake_sensor_1,
        "sensor_2": mock_fake_sensor_2,
    }
    return mock_registry

#------------------------------------------------------------------------------
#  "__init__" TESTS
def test_setup(base_config, mock_fake_sensor_registry): 
    # literally just test that initialization established in __init__. 
    # It is imparative that _build_sensors is called here to automatically 
    # link sensors in the sensor_config.toml file to actual drivers. 
    with patch.object(SensorManager, "_build_sensors") as mock_build_sensors:
        sm = SensorManager(base_config, 
                            i2c_bus,
                            mock_fake_sensor_registry, 
                            False)
        assert sm.skip_failed_init is False
        assert sm.i2c_bus is i2c_bus
        assert sm._sensors == {}
        mock_build_sensors.assert_called_once()

#------------------------------------------------------------------------------
#  test _build_sensors() method
# Sensor manager with build patch to not pre-emptively call _build_sensors when
# making an instance of the class
@pytest.fixture
def sensor_manager_bp(base_config, mock_fake_sensor_registry):
    with patch.object(SensorManager, "_build_sensors"):
        return SensorManager(base_config, 
                             i2c_bus, 
                             mock_fake_sensor_registry, 
                             False)

# test success path for a real and a sim sensor, covering both real and 
# sim sensors
def test_build_rr_sensors_success(sensor_manager_bp,
                                   mock_driver_registry):
    with patch.dict("src.SensorManager.driver_registry", mock_driver_registry):
        sensor_manager_bp._build_sensors()
        assert sensor_manager_bp.enabled_sensors == ["sensor_1", "sensor_2"]
        list_of_keys = list(sensor_manager_bp._sensors.keys())
        assert list_of_keys == ["sensor_1", "sensor_2"]
        assert len(list_of_keys) == 2
        assert sensor_manager_bp._sensors["sensor_1"] is not None
        assert sensor_manager_bp._sensors["sensor_2"] is not None

def test_build_no_enabled_sensors(sensor_manager_bp, no_enabled_sensors_config):
    sensor_manager_bp.config_dict = no_enabled_sensors_config
    with pytest.raises(ConfigError):
        sensor_manager_bp._build_sensors()

def test_missing_sensor_meta_data(sensor_manager_bp, 
                                  mock_driver_registry, 
                                  missing_meta_data_config):
    sensor_manager_bp.config_dict = missing_meta_data_config
    with patch.dict("src.SensorManager.driver_registry", mock_driver_registry): 
        with pytest.raises(ConfigError):
            sensor_manager_bp._build_sensors()

# test both the key-value pair missing altogether or an empty/wrong value
# tests the failure route of "if not driver_name"
def test_missing_driver_name(sensor_manager_bp, 
                             mock_driver_registry, 
                             missing_driver_field_config, 
                             empty_driver_field_config):
    
    with patch.dict("src.SensorManager.driver_registry", mock_driver_registry):
        sensor_manager_bp.config_dict = missing_driver_field_config
        with pytest.raises(ConfigError):
            sensor_manager_bp._build_sensors()
        sensor_manager_bp.config_dict = empty_driver_field_config
        with pytest.raises(ConfigError):
            sensor_manager_bp._build_sensors()

def test_wrong_driver_name(sensor_manager_bp,
                           mock_driver_registry,
                           wrong_driver_name_config):
    sensor_manager_bp.config_dict = wrong_driver_name_config
    with patch.dict("src.SensorManager.driver_registry", mock_driver_registry):
        with pytest.raises(ConfigError):
            sensor_manager_bp._build_sensors()

#------------------------------------------------------------------------------
#  Test initialize_all() method
@pytest.fixture
def sensor_manager(base_config, 
                   mock_driver_registry, 
                   mock_fake_sensor_registry):
    with patch.dict("src.SensorManager.driver_registry", mock_driver_registry):
        yield SensorManager(base_config, 
                            i2c_bus, 
                            mock_fake_sensor_registry, 
                            False)

def test_initialize_all_success(sensor_manager): 
    with patch("src.SensorManager.logger") as mock_logger: 
        sensor_manager.initialize_all()
        correct_log_count = 2 * len(sensor_manager.config_dict["sensors"])
        assert mock_logger.info.call_count == correct_log_count

@pytest.fixture
def exception_driver_initializations():
    mock_driver_1 = MagicMock()
    mock_driver_1.initialize.side_effect = Exception("simulated failure")
    mock_driver_2 = MagicMock()
    mock_driver_2.initialize.return_value = None
    mock_sensors = {"sensor_1": mock_driver_1,
                    "sensor_2": mock_driver_2}
    return mock_sensors

def test_initialize_all_fail_no_skip(sensor_manager, 
                                     exception_driver_initializations):

    sensor_manager._sensors = exception_driver_initializations
    with patch("src.SensorManager.logger") as mock_logger: 
        with pytest.raises(SensorInitError):
            sensor_manager.initialize_all()
        mock_logger.info.assert_called_once()

def test_initialize_all_fail_skip(sensor_manager, 
                                  exception_driver_initializations):
    sensor_manager.skip_failed_init = True
    surviving_sensors = copy.deepcopy(exception_driver_initializations)
    sensor_manager._sensors = exception_driver_initializations
    assert sensor_manager._sensors != {}
    with patch("src.SensorManager.logger") as mock_logger: 
        sensor_manager.initialize_all()
        assert mock_logger.info.call_count == 3
        assert mock_logger.critical.call_count == 1
        surviving_sensors.pop("sensor_1")
        assert sensor_manager._sensors == surviving_sensors

#------------------------------------------------------------------------------
#  Test read_all() method

@pytest.fixture
def success_sensor_driver_readers():
    mock_driver_1 = MagicMock()
    mock_driver_1.initialized = True
    mock_driver_1.read.return_value = [Reading("speed", 2, "m/s")]
    mock_driver_2 = MagicMock()
    mock_driver_2.initialized = True
    rv = [Reading("weight", 4, "kg"), Reading("temp", 273, "K")]
    mock_driver_2.read.return_value = rv
    mock_sensors = {"sensor_1": mock_driver_1,
                    "sensor_2": mock_driver_2}
    return mock_sensors

def test_read_all_sensors_success(sensor_manager, 
                                  success_sensor_driver_readers):
    sensor_manager._sensors = success_sensor_driver_readers
    with patch("src.SensorManager.logger") as mock_logger:
        results = sensor_manager.read_all()
        assert list(results.keys()) == ["sensor_1", "sensor_2"]
        assert len(results["sensor_1"])     == 1
        assert len(results["sensor_2"])     == 2
        assert results["sensor_1"][0].name  == "speed"
        assert results["sensor_1"][0].value == 2
        assert results["sensor_1"][0].unit  == "m/s"
        assert results["sensor_2"][0].name  == "weight"
        assert results["sensor_2"][0].value == 4
        assert results["sensor_2"][0].unit  == "kg"
        assert results["sensor_2"][1].name  == "temp"
        assert results["sensor_2"][1].value == 273
        assert results["sensor_2"][1].unit  == "K"
        assert mock_logger.info.call_count  == 2 

@pytest.fixture
def semi_fail_sensor_driver_readers():
    mock_driver_1 = MagicMock()
    mock_driver_1.initialized = True
    mock_driver_1.read.return_value = [Reading("speed", 2, "m/s")]
    mock_driver_2 = MagicMock()
    mock_driver_2.initialized = True
    mock_driver_2.read.side_effect = Exception("failed reading")
    mock_sensors = {"sensor_1": mock_driver_1,
                    "sensor_2": mock_driver_2}
    return mock_sensors

def test_read_all_sensors_fail(sensor_manager, semi_fail_sensor_driver_readers):
    sensor_manager._sensors = semi_fail_sensor_driver_readers
    with patch("src.SensorManager.logger") as mock_logger:
        results = sensor_manager.read_all()
        assert list(results.keys()) == ["sensor_1", "sensor_2"]
        assert len(results["sensor_1"])     == 1
        assert len(results["sensor_2"])     == 2
        assert results["sensor_1"][0].name  == "speed"
        assert results["sensor_1"][0].value == 2
        assert results["sensor_1"][0].unit  == "m/s"
        assert results["sensor_2"][0].name  == None
        assert results["sensor_2"][0].value == None
        assert results["sensor_2"][0].unit  == None
        assert results["sensor_2"][1].name  == None
        assert results["sensor_2"][1].value == None
        assert results["sensor_2"][1].unit  == None
        assert mock_logger.info.call_count  == 2 
        assert mock_logger.error.call_count == 1

@pytest.fixture
def some_init_drivers():
    mock_driver_1 = MagicMock()
    mock_driver_1.initialized = True
    mock_driver_1.read.return_value = [Reading("speed", 2, "m/s")]
    mock_driver_2 = MagicMock()
    mock_driver_2.initialized = False 
    mock_sensors = {"sensor_1": mock_driver_1,
                    "sensor_2": mock_driver_2}
    return mock_sensors

def test_not_initialized_catch(sensor_manager, some_init_drivers):
        sensor_manager._sensors = some_init_drivers
        with patch("src.SensorManager.logger") as mock_logger:
            results = sensor_manager.read_all()
            assert list(results.keys()) == ["sensor_1", "sensor_2"]
            assert len(results["sensor_1"])       == 1
            assert len(results["sensor_2"])       == 2
            assert results["sensor_1"][0].name    == "speed"
            assert results["sensor_1"][0].value   == 2
            assert results["sensor_1"][0].unit    == "m/s"
            assert results["sensor_2"][0].value   == None
            assert results["sensor_2"][0].unit    == None
            assert results["sensor_2"][1].name    == None
            assert results["sensor_2"][1].value   == None
            assert results["sensor_2"][1].unit    == None
            assert mock_logger.info.call_count    == 1 
            assert mock_logger.warning.call_count == 1

#------------------------------------------------------------------------------
#  Test initialize() method

def test_initialize_nonexistent(sensor_manager):
    with pytest.raises(SensorInitError):
        sensor_manager.initialize("not_a_sensor")

@pytest.fixture
def fake_sensors_drivers():
    mock_driver_1 = MagicMock()
    mock_driver_1.initialize.return_value = None
    mock_driver_2 = MagicMock()
    mock_driver_2.initialize.return_value = None
    mock_sensors = {"sensor_1": mock_driver_1,
                    "sensor_2": mock_driver_2}
    return mock_sensors

def test_initialize_unknown_sensor(sensor_manager, fake_sensors_drivers): 
    sensor_manager._sensors = fake_sensors_drivers
    with patch("src.SensorManager.logger") as mock_logger:
        with pytest.raises(SensorInitError):
            sensor_manager.initialize("not_a_sensor")
        assert mock_logger.error.call_count == 1

def test_initialize_success(sensor_manager, fake_sensors_drivers): 
    sensor_manager._sensors = fake_sensors_drivers
    with patch("src.SensorManager.logger") as mock_logger:
        sensor_manager.initialize("sensor_1")
        assert mock_logger.info.call_count == 2

def test_initialize_fail_skip(sensor_manager, exception_driver_initializations): 
    sensor_manager.skip_failed_init = True
    sensor_manager._sensors = exception_driver_initializations
    with patch("src.SensorManager.logger") as mock_logger:
        sensor_manager.initialize("sensor_1")
        assert mock_logger.info.call_count == 1
        assert mock_logger.critical.call_count == 1

def test_initialize_fail_raise(sensor_manager, exception_driver_initializations): 
    sensor_manager._sensors = exception_driver_initializations
    with patch("src.SensorManager.logger") as mock_logger:
        with pytest.raises(SensorInitError):
            sensor_manager.initialize("sensor_1")
        assert mock_logger.info.call_count == 1
        assert mock_logger.critical.call_count == 1

#------------------------------------------------------------------------------
#  Test read() method
def test_read_nonexistent(sensor_manager):
    with patch("src.SensorManager.logger") as mock_logger:
        with pytest.raises(SensorReadError):
            results = sensor_manager.read("not_a_sensor")
        mock_logger.critical.assert_called_once()

def test_read_success(sensor_manager, success_sensor_driver_readers):
    sensor_manager._sensors = success_sensor_driver_readers
    with patch("src.SensorManager.logger") as mock_logger:
        results = sensor_manager.read("sensor_1")
        mock_logger.info.assert_called_once()
        assert results["sensor_1"][0].name  == "speed"
        assert results["sensor_1"][0].value == 2
        assert results["sensor_1"][0].unit  == "m/s"
        assert len(results["sensor_1"])     == 1

def test_read_fail(sensor_manager, semi_fail_sensor_driver_readers):
    sensor_manager._sensors = semi_fail_sensor_driver_readers
    with patch("src.SensorManager.logger") as mock_logger:
        results = sensor_manager.read("sensor_2")
        mock_logger.info.assert_called_once()
        mock_logger.error.assert_called_once()
        assert results["sensor_2"][0].value == None
        assert results["sensor_2"][0].unit  == None
        assert results["sensor_2"][1].name  == None
        assert results["sensor_2"][1].value == None
        assert results["sensor_2"][1].unit  == None
        assert len(results["sensor_2"]) == 2
#------------------------------------------------------------------------------
