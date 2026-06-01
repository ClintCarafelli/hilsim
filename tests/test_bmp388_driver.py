"""Test the BMP388 Driver class"""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from src.bmp388_driver import BMP388Driver
from src.SensorExceptions import SensorInitError, SensorReadError

# ------------------------------------------------------------------------------
# Setup
SENSOR_ID = "BMP388"
I2C_BUS = None
FAKE_SENSOR = MagicMock()

READINGS_LIST = [
    {"name": "pressure", "units": "hpa", "min": 300, "max": 1250},
    {"name": "air_temp", "units": "C", "min": 0, "max": 65},
]


@pytest.fixture
def base_config() -> dict:
    """Set up a basic config with a real sensor"""
    return {
        "sim": False,
        "failure_rate": 0,
        "readings": READINGS_LIST,
        "sim_fail_initialization": False,
    }


@pytest.fixture
def sim_config(base_config: dict) -> dict:
    """Create new config that is for the sim case"""
    return {**base_config, "sim": True}


@pytest.fixture
def real_driver(base_config: dict) -> BMP388Driver:
    """Create driver for a 'real' sensor"""
    return BMP388Driver(SENSOR_ID, base_config, I2C_BUS, FAKE_SENSOR)


@pytest.fixture
def sim_driver(sim_config: dict) -> BMP388Driver:
    """Create a driver for a 'sim' sensor"""
    return BMP388Driver(SENSOR_ID, sim_config, I2C_BUS, FAKE_SENSOR)


# ------------------------------------------------------------------------------
# Test init


# Make sure default condiiions of the dirver are correct (i.e. initialized is
# false etc.)
def test_real_setup(real_driver: BMP388Driver) -> None:
    """Verify the instance of the real driver"""
    assert real_driver.sim is False


def test_sim_setup(sim_driver: BMP388Driver) -> None:
    """Verify the instance of the sim driver"""
    assert sim_driver.sim is True
    assert sim_driver.fake_sensor is FAKE_SENSOR
    assert sim_driver.sim_fail_initialization is False


# ------------------------------------------------------------------------------
# Test initialize() method
#
# Three major paths:
#   - sim initilization success
#   - real initialization success
#   - failure initialization either sim or real sensor, so technically one
#     test below is redundant. Kept for patching / mocking practice


def test_sim_initialize_success(sim_driver: BMP388Driver) -> None:
    """Test the successful initilization of a sim sensor"""
    sim_driver.initialize()
    assert sim_driver.device is FAKE_SENSOR
    assert sim_driver.initialized is True


def test_sim_initialize_failure(sim_driver: BMP388Driver) -> None:
    """Test the failed initilization of a sim sensor"""
    sim_driver.sim_fail_initialization = True
    with pytest.raises(SensorInitError):
        sim_driver.initialize()
    assert sim_driver.initialized is False


def test_initialize_success(real_driver: BMP388Driver) -> None:
    """Test the successful initialization of a real sensor"""
    mock_device = MagicMock()
    mock_bmp388_i2c_class = MagicMock(return_value=mock_device)
    with patch.dict(
        "sys.modules", {"adafruit_bmp3xx": MagicMock(BMP3XX_I2C=mock_bmp388_i2c_class)}
    ):
        real_driver.initialize()
        assert real_driver.initialized is True
        assert real_driver.device is mock_device
        mock_bmp388_i2c_class.assert_called_once_with(real_driver.i2c_bus)


def test_initialize_failure(real_driver: BMP388Driver) -> None:
    """Test the failed initialization of a real sensor,
    technically same branch as a sim failure"""
    mock_bmp388_i2c_class = MagicMock(side_effect=Exception("fail"))
    with patch.dict(
        "sys.modules", {"adafruit_bmp3xx": MagicMock(BMP3XX_I2C=mock_bmp388_i2c_class)}
    ):
        with pytest.raises(SensorInitError):
            real_driver.initialize()
        assert real_driver.initialized is False


# ------------------------------------------------------------------------------
# Test read() method
# Note: real_driver is used as default. Behavior is independent of whether the
# sensor is sim or real

# Two major paths:
#   - successful reading
#   - failed reading


def test_read_not_initialized(real_driver: BMP388Driver) -> None:
    """Test the not_initialized catch, which by standardization of
    methods across sensors is required"""
    with pytest.raises(SensorReadError):
        real_driver.read()


def test_read_success(real_driver: BMP388Driver) -> None:
    """Test successfully reading a sensor"""
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.pressure = 1
    real_driver.device.temperature = 2
    result = real_driver.read()
    assert result[0].value == 1
    assert result[1].value == 2


def test_read_failure(real_driver: BMP388Driver) -> None:
    """Test failed reading of the sensor"""
    real_driver.initialized = True
    real_driver.device = MagicMock()
    type(real_driver.device).pressure = PropertyMock(side_effect=Exception("fail"))
    with pytest.raises(SensorReadError):
        real_driver.read()


# ------------------------------------------------------------------------------
