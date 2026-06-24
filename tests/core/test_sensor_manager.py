"""Test the sensor manager"""

from unittest.mock import MagicMock, patch

import pytest
from hilsim.core.sensor_exceptions import SensorInitError, SensorReadError
from hilsim.core.sensor_manager import Reading, SensorManager

# Note: some things in this file are repetitive. I have done this to avoid
# slightly modifying things far away from where they are used for a specific test
# case, instead redefining the object with the modifications near its use as to
# make these tests more maintainable.

# ------------------------------------------------------------------------------
# Setup
I2C_BUS = MagicMock()

# Create fake driver registry

@pytest.fixture
def mock_driver_registry() -> dict:
    """create driver registry that produces successful readings"""
    mock_driver_1 = MagicMock()
    mock_driver_1.initialized = True
    mock_driver_1.read.return_value = {"speed": Reading(2, "m/s")}
    mock_driver_2 = MagicMock()
    mock_driver_2.initialized = True
    rv = {"weight": Reading(4, "kg"), "temp": Reading(273, "K")}
    mock_driver_2.read.return_value = rv
    mock_sensors = {"sensor_1": mock_driver_1, "sensor_2": mock_driver_2}
    return mock_sensors


@pytest.fixture
def sensor_manager(sensor_config: dict, mock_driver_registry: dict) -> SensorManager:
    """Construct instance of sensor manager, with _build_sensors called, to
    be used in the remainder of tests"""
    return SensorManager(sensor_config, I2C_BUS, mock_driver_registry, False)


# ------------------------------------------------------------------------------
#  Test instance construction
def test_setup(sensor_config: dict, mock_driver_registry: dict) -> None:
    """Test the construction of the instance"""
    # literally just test that initialization established in __init__.
    # It is imparative that _build_sensors is called here to automatically
    # link sensors in the sensor_config.toml file to actual drivers.
    sm = SensorManager(sensor_config, I2C_BUS, mock_driver_registry, False)
    assert sm.skip_failed_init is False
    assert sm.i2c_bus is I2C_BUS
    assert sm.sensors == mock_driver_registry
    assert sm.config_dict == sensor_config


# ------------------------------------------------------------------------------
#  Test initialize_all() method

# Three branches:
#    - successful initialization
#    - failed initalization with skip failed sensors
#    - failed initialization that raises the issue


def test_initialize_all_success(sensor_manager: SensorManager) -> None:
    """Test successful initialization"""
    with patch("hilsim.core.sensor_manager.logger") as mock_logger:
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
    with patch("hilsim.core.sensor_manager.logger") as mock_logger:
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
    with patch("hilsim.core.sensor_manager.logger") as mock_logger:
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
    mock_driver_1.read.return_value = {"speed": Reading(2, "m/s")}
    mock_driver_2 = MagicMock()
    mock_driver_2.initialized = True
    rv = {"weight": Reading(4, "kg"), "temp": Reading(273, "K")}
    mock_driver_2.read.return_value = rv
    mock_sensors = {"sensor_1": mock_driver_1, "sensor_2": mock_driver_2}
    return mock_sensors


def test_read_all_sensors_success(
    sensor_manager: SensorManager, success_sensor_driver_registry: dict
) -> None:
    """Test successful sensor reading"""
    sensor_manager.sensors = success_sensor_driver_registry
    with (
        patch("hilsim.core.sensor_manager.logger") as mock_logger,
        patch("hilsim.core.sensor_manager.time.time", return_value=0) as mock_time,
    ):
        results, time = sensor_manager.read_all()
        assert time == 0
        mock_time.assert_called_once()
        assert list(results.keys()) == ["sensor_1", "sensor_2"]
        assert len(results["sensor_1"]) == 1
        assert len(results["sensor_2"]) == 2
        assert results["sensor_1"]["speed"].value == 2
        assert results["sensor_1"]["speed"].unit == "m/s"
        assert results["sensor_2"]["weight"].value == 4
        assert results["sensor_2"]["weight"].unit == "kg"
        assert results["sensor_2"]["temp"].value == 273
        assert results["sensor_2"]["temp"].unit == "K"
        assert mock_logger.info.call_count == 2


@pytest.fixture
def semi_fail_sensor_driver_registry() -> dict:
    """Create a driver registry where one of the drivers has a failed reading"""
    mock_driver_1 = MagicMock()
    mock_driver_1.initialized = True
    mock_driver_1.read.return_value = {"speed": Reading(2, "m/s")}
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
    with (
        patch("hilsim.core.sensor_manager.logger") as mock_logger,
        patch("hilsim.core.sensor_manager.time.time", return_value=0) as mock_time,
    ):
        results, time = sensor_manager.read_all()
        assert time == 0
        mock_time.assert_called_once()
        print(results)
        assert list(results.keys()) == ["sensor_1", "sensor_2"]
        assert len(results["sensor_1"]) == 1
        assert len(results["sensor_2"]) == 1
        assert results["sensor_1"]["speed"].value == 2
        assert results["sensor_1"]["speed"].unit == "m/s"
        assert results["sensor_2"]["variable_3"].value is None
        assert results["sensor_2"]["variable_3"].unit == "var_3_units"
        assert mock_logger.info.call_count == 2
        assert mock_logger.error.call_count == 1


@pytest.fixture
def some_init_driver_registry() -> dict:
    """Create a driver registry where some of the sensors are not initialized"""
    mock_driver_1 = MagicMock()
    mock_driver_1.initialized = True
    mock_driver_1.read.return_value = {"speed": Reading(2, "m/s")}
    mock_driver_2 = MagicMock()
    mock_driver_2.initialized = False
    mock_sensors = {"sensor_1": mock_driver_1, "sensor_2": mock_driver_2}
    return mock_sensors


def test_not_initialized_catch(
    sensor_manager: SensorManager, some_init_driver_registry: dict
) -> None:
    """Test the not-initialized sensor catch and skip"""
    sensor_manager.sensors = some_init_driver_registry
    with (
        patch("hilsim.core.sensor_manager.logger") as mock_logger,
        patch("hilsim.core.sensor_manager.time.time", return_value=0) as mock_time,
    ):
        results, time = sensor_manager.read_all()
        assert time == 0
        mock_time.assert_called_once()
        assert list(results.keys()) == ["sensor_1", "sensor_2"]
        assert len(results["sensor_1"]) == 1
        assert len(results["sensor_2"]) == 1
        assert results["sensor_1"]["speed"].value == 2
        assert results["sensor_1"]["speed"].unit == "m/s"
        assert results["sensor_2"]["variable_3"].value is None
        assert results["sensor_2"]["variable_3"].unit == "var_3_units"
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
    with patch("hilsim.core.sensor_manager.logger") as mock_logger:
        with pytest.raises(SensorInitError):
            sensor_manager.initialize("not_a_sensor")
        assert mock_logger.error.call_count == 1


def test_initialize_success(
    sensor_manager: SensorManager, fake_sensors_drivers: dict
) -> None:
    """Test successfuly initializing a sensor"""
    sensor_manager.sensors = fake_sensors_drivers
    with patch("hilsim.core.sensor_manager.logger") as mock_logger:
        sensor_manager.initialize("sensor_1")
        assert mock_logger.info.call_count == 2


def test_initialize_fail_skip(
    sensor_manager: SensorManager, exception_driver_initializations: dict
) -> None:
    """Test skipping a failed initialization"""
    sensor_manager.skip_failed_init = True
    sensor_manager.sensors = exception_driver_initializations
    with patch("hilsim.core.sensor_manager.logger") as mock_logger:
        sensor_manager.initialize("sensor_1")
        assert mock_logger.info.call_count == 1
        assert mock_logger.critical.call_count == 1


def test_initialize_fail_raise(
    sensor_manager: SensorManager, exception_driver_initializations: dict
) -> None:
    """Test not skipping a failed initialization"""
    sensor_manager.sensors = exception_driver_initializations
    with patch("hilsim.core.sensor_manager.logger") as mock_logger:
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
    with patch("hilsim.core.sensor_manager.logger") as mock_logger:
        with pytest.raises(SensorReadError):
            results = sensor_manager.read("not_a_sensor")
        mock_logger.critical.assert_called_once()


def test_read_success(
    sensor_manager: SensorManager, success_sensor_driver_registry: dict
) -> None:
    """Test successfully reading a sensor"""
    sensor_manager.sensors = success_sensor_driver_registry
    with (
        patch("hilsim.core.sensor_manager.logger") as mock_logger,
        patch("hilsim.core.sensor_manager.time.time", return_value=0) as mock_time,
    ):
        results, time = sensor_manager.read("sensor_1")
        assert time == 0
        mock_time.assert_called_once()
        print(results)
        mock_logger.info.assert_called_once()
        assert results["sensor_1"]["speed"].value == 2
        assert results["sensor_1"]["speed"].unit == "m/s"
        assert len(results["sensor_1"]) == 1


def test_read_fail(
    sensor_manager: SensorManager, semi_fail_sensor_driver_registry: dict
) -> None:
    """Test a failed reading of a sensor"""
    sensor_manager.sensors = semi_fail_sensor_driver_registry
    with (
        patch("hilsim.core.sensor_manager.logger") as mock_logger,
        patch("hilsim.core.sensor_manager.time.time", return_value=0) as mock_time,
    ):
        results, time = sensor_manager.read("sensor_2")
        assert time == 0
        mock_time.assert_called_once()
        mock_logger.info.assert_called_once()
        mock_logger.error.assert_called_once()
        assert results["sensor_2"]["variable_3"].value is None
        assert results["sensor_2"]["variable_3"].unit == "var_3_units"
        assert len(results["sensor_2"]) == 1


# ------------------------------------------------------------------------------
# Test _build_None_reading() method:

# No branches


def test_buid_none_reading(sensor_manager: SensorManager) -> None:
    """Test the build_None_reading method()"""
    with patch.object(
        sensor_manager,
        "_map_readings_to_name",
        return_value={
            "var_1": {"units": "var_1_units"},
            "var_2": {"units": "var_2_units"},
        },
    ):
        results = sensor_manager._build_None_reading("sensor_1")
        assert results.keys() == {"var_1", "var_2"}
        results["var_1"].value is None
        results["var_2"].value is None
        results["var_1"].unit == "var_1_units"
        results["var_2"].unit == "var_2_units"


# ------------------------------------------------------------------------------
# Test _map_readings_to_name() method:

# No branches:


def test_map_readings_to_name(
    sensor_config: dict, sensor_manager: SensorManager
) -> None:
    """Test map_readings_to_name method()"""
    results = sensor_manager._map_readings_to_name("sensor_1")
    assert results.keys() == {"variable_1", "variable_2"}
    assert results["variable_1"] == sensor_config["sensors"]["sensor_1"]["readings"][0]
    assert results["variable_2"] == sensor_config["sensors"]["sensor_1"]["readings"][1]


# ------------------------------------------------------------------------------
# Test build_header() method:


# No branches


@pytest.fixture
def sample_data() -> dict:
    """Create sample data that is used to build the header"""
    return {
        "sensor_1": {"speed": Reading(2, "m/s")},
        "sensor_2": {"weight": Reading(4, "kg"), "temp": Reading(273, "K")},
    }


def test_build_header(sensor_manager: SensorManager, sample_data: dict) -> None:
    """Test the build_header() method"""
    results = sensor_manager.build_header(sample_data)
    assert results[0] == ["sensor_1", "sensor_2", "sensor_2", "system_clock"]
    assert results[1] == ["speed (m/s)", "weight (kg)", "temp (K)", "time (UNIX)"]


# ------------------------------------------------------------------------------
