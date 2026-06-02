"""Test the sensor manager"""

import copy
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from src.base_driver import Reading
from src.sensor_manager import SensorManager
from src.SensorExceptions import ConfigError, SensorInitError, SensorReadError


# Note: some things in this file are repetitive. I have done this to avoid
# slightly modifying things far away from where they are used for a specific test
# case, instead redefining the object with the modifications near its use as to
# make these tests more maintainable.

# ------------------------------------------------------------------------------
# Setup

I2C_BUS = MagicMock()
CONFIG_DICT = {
    "sensor_params": {"enabled_sensors": ["sensor_1", "sensor_2"], "sim_all": True},
    "sensors": {
        "sensor_1": {
            "description": "fake sensor 1, " + "reads speed",
            "sensor_num": 1,
            "num_measurements": 1,
            "driver": "sensor_1_driver",
            "sim": True,
            "failure_rate": 0,
            "readings": [{"name": "speed", "units": "m/s"}],
        },
        "sensor_2": {
            "description": "fake sensor 2, " + "reads weight and temperature",
            "sensor_num": 1,
            "num_measurements": 2,
            "driver": "sensor_2_driver",
            "sim": False,
            "failure_rate": 0,
            "readings": [
                {"name": "weight", "units": "kg"},
                {"name": "temp", "units": "C"},
            ],
        },
    },
}


@pytest.fixture
def base_config() -> dict:
    """Set up config dict as a fixture for ease of use"""
    return CONFIG_DICT


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# The following fixtures are all used to test the _build_sensors() method
# but belong to the set up
@pytest.fixture
def no_enabled_sensors_config(base_config: dict) -> dict:
    """Create a config with no enabled sensors"""
    copy_config = copy.deepcopy(base_config)
    copy_config["sensor_params"]["enabled_sensors"] = []
    return copy_config


@pytest.fixture
def missing_meta_data_config(base_config: dict) -> dict:
    """Create a config that is missing sensor reading meta data"""
    copy_config = copy.deepcopy(base_config)
    copy_config["sensors"] = {
        "sensor_1": {
            "description": "fake sensor 1, reads speed",
            "sensor_num": 1,
            "sensor_num_measurements": 1,
            "driver": "sensor_1_driver",
            "sim": True,
            "failure_rate": 0,
        }
    }
    return copy_config


@pytest.fixture
def missing_driver_field_config(base_config: dict) -> dict:
    """Create a config that has a sensor missing its driver field"""
    copy_config = copy.deepcopy(base_config)
    del copy_config["sensors"]["sensor_1"]["driver"]
    return copy_config


@pytest.fixture
def empty_driver_field_config(base_config: dict) -> dict:
    """Create a config that has a sensor with an empty driver field"""
    copy_config = copy.deepcopy(base_config)
    copy_config["sensors"]["sensor_1"]["driver"] = None
    return copy_config


@pytest.fixture
def wrong_driver_name_config(base_config: dict) -> dict:
    """Create a config that has a sensor with a non-existent driver name"""
    copy_config = copy.deepcopy(base_config)
    copy_config["sensors"]["sensor_1"]["driver"] = "not_a_driver"
    return copy_config


@pytest.fixture
def mock_driver_registry() -> dict:
    """Create a fake driver registry to use"""
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
def mock_fake_sensor_registry() -> dict:
    """Create a fake sensor registry to use"""
    mock_fake_sensor_1 = MagicMock()
    mock_fake_sensor_2 = MagicMock()
    mock_registry = {
        "sensor_1": mock_fake_sensor_1,
        "sensor_2": mock_fake_sensor_2,
    }
    return mock_registry


# ------------------------------------------------------------------------------
#  Test instance construction
def test_setup(base_config: dict, mock_fake_sensor_registry: dict) -> None:
    """Test the construction of the instance"""
    # literally just test that initialization established in __init__.
    # It is imparative that _build_sensors is called here to automatically
    # link sensors in the sensor_config.toml file to actual drivers.
    with patch.object(SensorManager, "_build_sensors") as mock_build_sensors:
        sm = SensorManager(base_config, I2C_BUS, mock_fake_sensor_registry, False)
        assert sm.skip_failed_init is False
        assert sm.i2c_bus is I2C_BUS
        assert not sm.sensors
        mock_build_sensors.assert_called_once()


# ------------------------------------------------------------------------------
#  test _build_sensors() method
# Sensor manager with build patch to not pre-emptively call _build_sensors when
# making an instance of the class

# Five branches:
#   - no enabled sensors
#   - Missing sensor section in config file
#   - Missing driver
#   - Non-existent driver name
#   - Successful build with sensor_id mapped to instance of driver


@pytest.fixture
def sensor_manager_bp(
    base_config: dict, mock_fake_sensor_registry: dict
) -> SensorManager:
    """create a sensor manager that has NOT already called _build_sensors
    during construction. Used to test _build_sensors"""
    with patch.object(SensorManager, "_build_sensors"):
        return SensorManager(base_config, I2C_BUS, mock_fake_sensor_registry, False)


# test success path for a real and a sim sensor, covering both real and
# sim sensors
def test_build_sensors_success(
    sensor_manager_bp: SensorManager, mock_driver_registry: dict
) -> None:
    """Test building all real sensors"""
    with patch.dict("src.sensor_manager.driver_registry", mock_driver_registry):
        sensor_manager_bp._build_sensors()
        assert sensor_manager_bp.enabled_sensors == ["sensor_1", "sensor_2"]
        list_of_keys = list(sensor_manager_bp.sensors.keys())
        assert list_of_keys == ["sensor_1", "sensor_2"]
        assert len(list_of_keys) == 2
        assert sensor_manager_bp.sensors["sensor_1"] is not None
        assert sensor_manager_bp.sensors["sensor_2"] is not None


def test_build_no_enabled_sensors(
    sensor_manager_bp: SensorManager, no_enabled_sensors_config: dict
) -> None:
    """Test missing enabled sensors for build_sensors"""
    sensor_manager_bp.config_dict = no_enabled_sensors_config
    with pytest.raises(ConfigError):
        sensor_manager_bp._build_sensors()


def test_missing_sensor_meta_data(
    sensor_manager_bp: SensorManager,
    mock_driver_registry: dict,
    missing_meta_data_config: dict,
) -> None:
    """Test _build_sensors with missing sensor reading meta data"""
    sensor_manager_bp.config_dict = missing_meta_data_config
    with patch.dict("src.sensor_manager.driver_registry", mock_driver_registry):
        with pytest.raises(ConfigError):
            sensor_manager_bp._build_sensors()


# test both the key-value pair missing altogether or an empty/wrong value
# tests the failure route of "if not driver_name"
def test_missing_driver_name(
    sensor_manager_bp: SensorManager,
    mock_driver_registry: dict,
    missing_driver_field_config: dict,
    empty_driver_field_config: dict,
) -> None:
    """Test _build_sensors with missing driver name"""
    with patch.dict("src.sensor_manager.driver_registry", mock_driver_registry):
        sensor_manager_bp.config_dict = missing_driver_field_config
        with pytest.raises(ConfigError):
            sensor_manager_bp._build_sensors()
        sensor_manager_bp.config_dict = empty_driver_field_config
        with pytest.raises(ConfigError):
            sensor_manager_bp._build_sensors()


def test_wrong_driver_name(
    sensor_manager_bp: SensorManager,
    mock_driver_registry: dict,
    wrong_driver_name_config: dict,
) -> None:
    """Test _build_sensors with a non-existent driver name"""
    sensor_manager_bp.config_dict = wrong_driver_name_config
    with patch.dict("src.sensor_manager.driver_registry", mock_driver_registry):
        with pytest.raises(ConfigError):
            sensor_manager_bp._build_sensors()


# ------------------------------------------------------------------------------
#  Test initialize_all() method

# Three branches:
#    - successful initialization
#    - failed initalization with skip failed sensors
#    - failed initialization that raises the issue


@pytest.fixture
def sensor_manager(
    base_config: dict, mock_driver_registry: dict, mock_fake_sensor_registry: dict
) -> Generator[SensorManager, None, None]:
    """Construct instance of sensor manager, with _build_sensors called, to
    be used in the remainder of tests"""
    with patch.dict("src.sensor_manager.driver_registry", mock_driver_registry):
        yield SensorManager(base_config, I2C_BUS, mock_fake_sensor_registry, False)


def test_initialize_all_success(sensor_manager: SensorManager) -> None:
    """Test successful initialization"""
    with patch("src.sensor_manager.logger") as mock_logger:
        sensor_manager.initialize_all()
        correct_log_count = 2 * len(sensor_manager.config_dict["sensors"])
        assert mock_logger.info.call_count == correct_log_count


@pytest.fixture
def exception_driver_initializations() -> dict:
    """Create drivers that fail initializations"""
    mock_driver_1 = MagicMock()
    mock_driver_1.initialize.side_effect = SensorInitError(
        "sensor_1", "simulated failure"
    )
    mock_driver_2 = MagicMock()
    mock_driver_2.initialize.return_value = None
    mock_sensors = {"sensor_1": mock_driver_1, "sensor_2": mock_driver_2}
    return mock_sensors


def test_initialize_all_fail_no_skip(
    sensor_manager: SensorManager, exception_driver_initializations: dict
) -> None:
    """Test failed initializations that don't skip"""
    sensor_manager.sensors = exception_driver_initializations
    with patch("src.sensor_manager.logger") as mock_logger:
        with pytest.raises(SensorInitError):
            sensor_manager.initialize_all()
        mock_logger.info.assert_called_once()


def test_initialize_all_fail_skip(
    sensor_manager: SensorManager, exception_driver_initializations: dict
) -> None:
    """Test failed initializations that do skip"""
    sensor_manager.skip_failed_init = True
    surviving_sensors = exception_driver_initializations.copy()
    sensor_manager.sensors = exception_driver_initializations
    assert sensor_manager.sensors != {}
    with patch("src.sensor_manager.logger") as mock_logger:
        sensor_manager.initialize_all()
        assert mock_logger.info.call_count == 3
        assert mock_logger.critical.call_count == 1
        surviving_sensors.pop("sensor_1")
        assert sensor_manager.sensors == surviving_sensors


# ------------------------------------------------------------------------------
#  Test read_all() method

# Three branches:
#    - catch not initialized, skip reading
#    - read success
#    - read failure


@pytest.fixture
def success_sensor_driver_registry() -> dict:
    """create driver registry that produces successful readings"""
    mock_driver_1 = MagicMock()
    mock_driver_1.initialized = True
    mock_driver_1.read.return_value = [Reading("speed", 2, "m/s")]
    mock_driver_2 = MagicMock()
    mock_driver_2.initialized = True
    rv = [Reading("weight", 4, "kg"), Reading("temp", 273, "K")]
    mock_driver_2.read.return_value = rv
    mock_sensors = {"sensor_1": mock_driver_1, "sensor_2": mock_driver_2}
    return mock_sensors


def test_read_all_sensors_success(
    sensor_manager: SensorManager, success_sensor_driver_registry: dict
) -> None:
    """Test successful sensor reading"""
    sensor_manager.sensors = success_sensor_driver_registry
    with patch("src.sensor_manager.logger") as mock_logger:
        results = sensor_manager.read_all()
        assert list(results.keys()) == ["sensor_1", "sensor_2"]
        assert len(results["sensor_1"]) == 1
        assert len(results["sensor_2"]) == 2
        assert results["sensor_1"][0].name == "speed"
        assert results["sensor_1"][0].value == 2
        assert results["sensor_1"][0].unit == "m/s"
        assert results["sensor_2"][0].name == "weight"
        assert results["sensor_2"][0].value == 4
        assert results["sensor_2"][0].unit == "kg"
        assert results["sensor_2"][1].name == "temp"
        assert results["sensor_2"][1].value == 273
        assert results["sensor_2"][1].unit == "K"
        assert mock_logger.info.call_count == 2


@pytest.fixture
def semi_fail_sensor_driver_registry() -> dict:
    """Create a driver registry where one of the drivers has a failed reading"""
    mock_driver_1 = MagicMock()
    mock_driver_1.initialized = True
    mock_driver_1.read.return_value = [Reading("speed", 2, "m/s")]
    mock_driver_2 = MagicMock()
    mock_driver_2.initialized = True
    mock_driver_2.read.side_effect = SensorReadError("sensor_2", "failed reading")
    mock_sensors = {"sensor_1": mock_driver_1, "sensor_2": mock_driver_2}
    return mock_sensors


def test_read_all_sensors_fail(
    sensor_manager: SensorManager, semi_fail_sensor_driver_registry: dict
) -> None:
    """Test a failed and successful sensor reading"""
    sensor_manager.sensors = semi_fail_sensor_driver_registry
    with patch("src.sensor_manager.logger") as mock_logger:
        results = sensor_manager.read_all()
        assert list(results.keys()) == ["sensor_1", "sensor_2"]
        assert len(results["sensor_1"]) == 1
        assert len(results["sensor_2"]) == 2
        assert results["sensor_1"][0].name == "speed"
        assert results["sensor_1"][0].value == 2
        assert results["sensor_1"][0].unit == "m/s"
        assert results["sensor_2"][0].name is None
        assert results["sensor_2"][0].value is None
        assert results["sensor_2"][0].unit is None
        assert results["sensor_2"][1].name is None
        assert results["sensor_2"][1].value is None
        assert results["sensor_2"][1].unit is None
        assert mock_logger.info.call_count == 2
        assert mock_logger.error.call_count == 1


@pytest.fixture
def some_init_driver_registry() -> dict:
    """Create a driver registry where some of the sensors are not initialized"""
    mock_driver_1 = MagicMock()
    mock_driver_1.initialized = True
    mock_driver_1.read.return_value = [Reading("speed", 2, "m/s")]
    mock_driver_2 = MagicMock()
    mock_driver_2.initialized = False
    mock_sensors = {"sensor_1": mock_driver_1, "sensor_2": mock_driver_2}
    return mock_sensors


def test_not_initialized_catch(
    sensor_manager: SensorManager, some_init_driver_registry: dict
) -> None:
    """Test the not-initialized sensor catch and skip"""
    sensor_manager.sensors = some_init_driver_registry
    with patch("src.sensor_manager.logger") as mock_logger:
        results = sensor_manager.read_all()
        assert list(results.keys()) == ["sensor_1", "sensor_2"]
        assert len(results["sensor_1"]) == 1
        assert len(results["sensor_2"]) == 2
        assert results["sensor_1"][0].name == "speed"
        assert results["sensor_1"][0].value == 2
        assert results["sensor_1"][0].unit == "m/s"
        assert results["sensor_2"][0].value is None
        assert results["sensor_2"][0].unit is None
        assert results["sensor_2"][1].name is None
        assert results["sensor_2"][1].value is None
        assert results["sensor_2"][1].unit is None
        assert mock_logger.info.call_count == 1
        assert mock_logger.warning.call_count == 1


# ------------------------------------------------------------------------------
#  Test initialize() method

# Three branches:
#    - successful initialization
#    - failed initalization with skip failed sensors
#    - failed initialization that raises the issue


@pytest.fixture
def fake_sensors_drivers() -> dict:
    """Create a driver registry with sensors that successfully initialize"""
    mock_driver_1 = MagicMock()
    mock_driver_1.initialize.return_value = None
    mock_driver_2 = MagicMock()
    mock_driver_2.initialize.return_value = None
    mock_sensors = {"sensor_1": mock_driver_1, "sensor_2": mock_driver_2}
    return mock_sensors


def test_initialize_unknown_sensor(
    sensor_manager: SensorManager, fake_sensors_drivers: dict
) -> None:
    """Test catching an attempt to initialize a non-existent sensor"""
    sensor_manager.sensors = fake_sensors_drivers
    with patch("src.sensor_manager.logger") as mock_logger:
        with pytest.raises(SensorInitError):
            sensor_manager.initialize("not_a_sensor")
        assert mock_logger.error.call_count == 1


def test_initialize_success(
    sensor_manager: SensorManager, fake_sensors_drivers: dict
) -> None:
    """Test successfuly initializing a sensor"""
    sensor_manager.sensors = fake_sensors_drivers
    with patch("src.sensor_manager.logger") as mock_logger:
        sensor_manager.initialize("sensor_1")
        assert mock_logger.info.call_count == 2


def test_initialize_fail_skip(
    sensor_manager: SensorManager, exception_driver_initializations: dict
) -> None:
    """Test skipping a failed initialization"""
    sensor_manager.skip_failed_init = True
    sensor_manager.sensors = exception_driver_initializations
    with patch("src.sensor_manager.logger") as mock_logger:
        sensor_manager.initialize("sensor_1")
        assert mock_logger.info.call_count == 1
        assert mock_logger.critical.call_count == 1


def test_initialize_fail_raise(
    sensor_manager: SensorManager, exception_driver_initializations: dict
) -> None:
    """Test not skipping a failed initialization"""
    sensor_manager.sensors = exception_driver_initializations
    with patch("src.sensor_manager.logger") as mock_logger:
        with pytest.raises(SensorInitError):
            sensor_manager.initialize("sensor_1")
        assert mock_logger.info.call_count == 1
        assert mock_logger.critical.call_count == 1


# ------------------------------------------------------------------------------
#  Test read() method

# Three branches:
#    - catch not initialized, skip reading
#    - read success
#    - read failure


def test_read_nonexistent(sensor_manager: SensorManager) -> None:
    """Test catching an attempt to read a non-existent sensor"""
    with patch("src.sensor_manager.logger") as mock_logger:
        with pytest.raises(SensorReadError):
            results = sensor_manager.read("not_a_sensor")
        mock_logger.critical.assert_called_once()


def test_read_success(
    sensor_manager: SensorManager, success_sensor_driver_registry: dict
) -> None:
    """Test successfully reading a sensor"""
    sensor_manager.sensors = success_sensor_driver_registry
    with patch("src.sensor_manager.logger") as mock_logger:
        results = sensor_manager.read("sensor_1")
        mock_logger.info.assert_called_once()
        assert results["sensor_1"][0].name == "speed"
        assert results["sensor_1"][0].value == 2
        assert results["sensor_1"][0].unit == "m/s"
        assert len(results["sensor_1"]) == 1


def test_read_fail(
    sensor_manager: SensorManager, semi_fail_sensor_driver_registry: dict
) -> None:
    """Test a failed reading of a sensor"""
    sensor_manager.sensors = semi_fail_sensor_driver_registry
    with patch("src.sensor_manager.logger") as mock_logger:
        results = sensor_manager.read("sensor_2")
        mock_logger.info.assert_called_once()
        mock_logger.error.assert_called_once()
        assert results["sensor_2"][0].value is None
        assert results["sensor_2"][0].unit is None
        assert results["sensor_2"][1].name is None
        assert results["sensor_2"][1].value is None
        assert results["sensor_2"][1].unit is None
        assert len(results["sensor_2"]) == 2


# ------------------------------------------------------------------------------
# Test build_header() method:


# Two paths:
#    - all sensors in config are enabled
#    - not all sensors in config are enabled


def test_build_header(sensor_manager: SensorManager) -> None:
    """Test build header where all sensors in config are enabled"""
    results = sensor_manager.build_header()
    assert results[0] == "speed (m/s)"
    assert results[1] == "weight (kg)"
    assert results[2] == "temp (C)"
    assert len(results) == 3


# Set up an instance where all drivers in config are not enabled
@pytest.fixture
def not_all_enabled_config(base_config: dict) -> dict:
    """Create a config where not all sensors in config are enabled"""
    copy_config = base_config.copy()
    copy_config["sensor_params"]["enabled_sensors"] = ["sensor_1"]
    return copy_config


@pytest.fixture
def sensor_manager_nae(
    not_all_enabled_config: dict,
    mock_driver_registry: dict,
    mock_fake_sensor_registry: dict,
) -> Generator[SensorManager, None, None]:
    """Construct instance of sensor manager, with _build_sensors called, to
    be used in the remainder of tests"""
    with patch.dict("src.sensor_manager.driver_registry", mock_driver_registry):
        yield SensorManager(
            not_all_enabled_config, I2C_BUS, mock_fake_sensor_registry, False
        )


def test_build_header_nae(sensor_manager_nae: SensorManager) -> None:
    """Test building a header where only some sensors are enabled"""
    results = sensor_manager_nae.build_header()
    assert results[0] == "speed (m/s)"
    assert len(results) == 1


# ------------------------------------------------------------------------------
