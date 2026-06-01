"""Test the SCD30 Driver"""

from unittest.mock import MagicMock, patch

import pytest
from src.scd30_driver import SCD30Driver
from src.SensorExceptions import SensorInitError, SensorReadError

# ------------------------------------------------------------------------------
# Setup
SENSOR_ID = "SCD30"
I2C_BUS = None
FAKE_SENSOR = MagicMock()
READING_LIST = [
    {
        "name": "CO2",
        "units": "ppm",
        "min": 0,
        "max": 40000,
    },
    {
        "name": "relative_humidity",
        "units": "percent",
        "min": 0,
        "max": 95,
    },
    {
        "name": "temp",
        "units": "C",
        "min": 0,
        "max": 50,
    },
]


@pytest.fixture
def base_config() -> dict:
    """Create the basic config to set up driver"""
    return {"readings": READING_LIST, "sim": False, "sim_fail_initialization": False}


@pytest.fixture
def sim_config(base_config: dict) -> dict:
    """Create config for a sim sensor"""
    return {**base_config, "sim": True}


@pytest.fixture
def sim_driver(sim_config: dict) -> SCD30Driver:
    """Create an instance of the SCD30 Drier with sim sensor paths"""
    return SCD30Driver(SENSOR_ID, sim_config, I2C_BUS, FAKE_SENSOR)


@pytest.fixture
def real_driver(base_config: dict) -> SCD30Driver:
    """Create an instance of the SCD30 Driver with real sensor paths"""
    return SCD30Driver(SENSOR_ID, base_config, I2C_BUS, FAKE_SENSOR)


# ------------------------------------------------------------------------------
# Test initialize() method

# Four branches:
#    - sim sensor:
#       - successful initialization
#       - failed initialization
#    - real sensor:
#       - successful initialization
#       - failed initialization


def test_sim_initialization_success(sim_driver: SCD30Driver) -> None:
    """Test simulated sensor initialization success"""
    sim_driver.initialize()
    assert sim_driver.device is FAKE_SENSOR
    assert sim_driver.initialized is True
    sim_driver.device.set_measurement_interval.assert_called_once_with(2)
    sim_driver.device.start_periodic_measurement.assert_called_once_with()


def test_sim_initialization_failure(sim_driver: SCD30Driver) -> None:
    """Test simulated sensor initialization failure"""
    sim_driver.sim_fail_initialization = True
    with pytest.raises(SensorInitError):
        sim_driver.initialize()
    assert sim_driver.initialized is False


def test_real_initialization_success(real_driver: SCD30Driver) -> None:
    """Test real sensor initialization success"""
    mock_device = MagicMock()
    fake_SCD30_class = MagicMock(return_value=mock_device)
    with patch.dict("sys.modules", {"scd30_i2c": MagicMock(SCD30=fake_SCD30_class)}):
        real_driver.initialize()
        assert real_driver.device is mock_device
        assert real_driver.initialized is True
        real_driver.device.set_measurement_interval.assert_called_once_with(2)
        real_driver.device.start_periodic_measurement.assert_called_once_with()


def test_real_initialization_failure(real_driver: SCD30Driver) -> None:
    """Test simulated sensor initialization failure"""
    fake_SCD30_class = MagicMock(side_effect=Exception("fail"))
    with patch.dict("sys.modules", {"scd30_i2c": MagicMock(SCD30=fake_SCD30_class)}):
        with pytest.raises(SensorInitError):
            real_driver.initialize()
        assert real_driver.initialized is False


# ------------------------------------------------------------------------------
# Test read() method

# Three paths:
#   - sensor not initialized, raise error
#   - successful sensor reading
#   - failed sensor reading

# real_driver is used as default, method does not branch based on what
# device (i.e. sim or real) is used


def test_read_not_initialized(real_driver: SCD30Driver) -> None:
    """Test not initialized catch"""
    with pytest.raises(SensorReadError):
        real_driver.read()


def test_read_success(real_driver: SCD30Driver) -> None:
    """Testing successful sensor reading"""
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.read_measurement.return_value = [1, 2, 3]
    result = real_driver.read()
    assert result[0].value == 1
    assert result[1].value == 2
    assert result[2].value == 3
    assert len(result) == 3


def test_read_failure(real_driver: SCD30Driver) -> None:
    """Test failed sensor reading"""
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.read_measurement.side_effect = Exception("fail")
    with pytest.raises(SensorReadError):
        result = real_driver.read()


# ------------------------------------------------------------------------------
