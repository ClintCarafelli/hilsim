"""Test the STEMMA driver"""

from unittest.mock import MagicMock, patch

import pytest
from src.SensorExceptions import SensorInitError, SensorReadError
from src.stemma import STEMMADriver

# ------------------------------------------------------------------------------
# Setup
SENSOR_ID = "STEMMA"
I2C_BUS = None
I2C_ADRESS = 0x36
FAKE_SENSOR = MagicMock()
READINGS_LIST = [
    {"name": "moisture", "units": "None", "max": 2000, "min": 200},
    {"name": "temp", "units": "C", "max": 85, "min": -40},
]


@pytest.fixture
def base_config() -> dict:
    """Create a basic config dictonary for driver"""
    return {
        "sim": False,
        "i2c_address": I2C_ADRESS,
        "readings": READINGS_LIST,
        "sim_fail_initialization": False,
    }


@pytest.fixture
def success_config(base_config: dict) -> dict:
    """Create a sim config dictonary for driver"""
    return {**base_config, "sim": True}


@pytest.fixture
def sim_driver(success_config: dict) -> STEMMADriver:
    """Create a driver with sim sensor paths"""
    return STEMMADriver(SENSOR_ID, success_config, I2C_BUS, FAKE_SENSOR)


@pytest.fixture
def real_driver(base_config: dict) -> STEMMADriver:
    """Create a driver with real sensor paths"""
    return STEMMADriver(SENSOR_ID, base_config, I2C_BUS, FAKE_SENSOR)


# ------------------------------------------------------------------------------
# Test initialize() method

# Four branches:
#    - sim sensor:
#       - initialization success
#       - initialization failure
#    - real sensor:
#       - initialization success
#       - initialization failure


def test_sim_initialize_success(sim_driver: STEMMADriver) -> None:
    """Test successful initialization of a sim sensor"""
    sim_driver.initialize()
    assert sim_driver.initialized is True
    assert sim_driver.device is FAKE_SENSOR


def test_sim_initialize_fail(sim_driver: STEMMADriver) -> None:
    """Test the failed initialization of a sim sensor"""
    sim_driver.sim_fail_initialization = True
    with pytest.raises(SensorInitError):
        sim_driver.initialize()
    assert sim_driver.initialized is False


def test_real_initialize_success(real_driver: STEMMADriver) -> None:
    """Test successful initialization of a real sensor"""
    mock_seesaw = MagicMock()
    with patch.dict(
        "sys.modules",
        {
            "adafruit_seesaw": MagicMock(),
            "adafruit_seesaw.seesaw": MagicMock(Seesaw=mock_seesaw),
        },
    ):
        real_driver.initialize()
        assert real_driver.initialized is True


def test_real_initialize_failure(real_driver: STEMMADriver) -> None:
    """Test failed initialization of a real sensor"""
    mock_seesaw = MagicMock(side_effect=Exception("fail"))
    with patch.dict(
        "sys.modules",
        {
            "adafruit_seesaw": MagicMock(),
            "adafruit_seesaw.seesaw": MagicMock(Seesaw=mock_seesaw),
        },
    ):
        with pytest.raises(SensorInitError):
            real_driver.initialize()
        assert real_driver.initialized is False


# ------------------------------------------------------------------------------
# Test read() method

# Three branches:
#   - catch a non-initialized sensor
#   - successful reading (return values)
#   - failed reading (raise SensorReadError)

# Note real_driver is used as default since behavior does not branch regardless
# of what type of sensor is used


def test_read_not_init_failure(real_driver: STEMMADriver) -> None:
    """Test not-initialized sensor catch"""
    with pytest.raises(SensorReadError):
        real_driver.read()


def test_read_success(real_driver: STEMMADriver) -> None:
    """Test successful reading of a sensor"""
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.moisture_read.return_value = 1000
    real_driver.device.get_temp.return_value = 30
    result = real_driver.read()
    assert len(result) == 2
    assert result[0].value == 1000
    assert result[1].value == 30


def test_read_failure(real_driver: STEMMADriver) -> None:
    """Test failed reading of a sensor"""
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.moisture_read.side_effect = Exception("fail")
    with pytest.raises(SensorReadError):
        real_driver.read()


# ------------------------------------------------------------------------------
