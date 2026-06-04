""" Test the INA260 Driver"""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from src.ina260 import INA260Driver
from src.SensorExceptions import SensorInitError, SensorReadError

# ---------------------------------------------------------------------------------------
# Setup

I2C_BUS = None
SENSOR_ID = "INA260"
FAKE_SENSOR = MagicMock()
READINGS_LIST = [
    {"name": "voltage", "units": "V"},
    {"name": "current", "units": "mA"},
    {"name": "power", "units": "mW"},
]


@pytest.fixture
def basic_config() -> dict:
    """Set up the basic config for real sensor"""
    return {
        "sim": False,
        "failure_rate": 0,
        "readings": READINGS_LIST,
        "sim_fail_initialization": False,
    }


@pytest.fixture
def sim_config(basic_config: dict) -> dict:
    """Set up config for sim sensor"""
    return {**basic_config, "sim": True}


@pytest.fixture
def real_driver(basic_config: dict) -> INA260Driver:
    """Create a driver for real sensor paths"""
    return INA260Driver(SENSOR_ID, basic_config, I2C_BUS, FAKE_SENSOR)


@pytest.fixture
def sim_driver(sim_config: dict) -> INA260Driver:
    """Create a driver for sim sensor paths"""
    return INA260Driver(SENSOR_ID, sim_config, I2C_BUS, FAKE_SENSOR)


# ---------------------------------------------------------------------------------------
# Test initialize() method:

# Four Branches:
#    - Sim Sensor:
#        - initialization success
#        - initialization failure
#    - Real sensor:
#        - initialization success
#        - initialization failure


def test_sim_success_initialization(sim_driver: INA260Driver) -> None:
    """Test a successful initialization of a sim sensor"""
    sim_driver.initialize()
    assert sim_driver.device is FAKE_SENSOR
    assert sim_driver.initialized is True


def test_sim_fail_initialization(sim_driver: INA260Driver) -> None:
    """Test a failed initialization of a sim sensor"""
    sim_driver.sim_fail_initialization = True
    with pytest.raises(SensorInitError):
        sim_driver.initialize()
    assert sim_driver.initialized is False


def test_success_initialization(real_driver: INA260Driver) -> None:
    """Test a successful initialization of a real sensor"""
    mock_device = MagicMock()
    fake_ina260_class = MagicMock(return_value=mock_device)
    with patch.dict(
        "sys.modules", {"adafruit_ina260": MagicMock(INA260=fake_ina260_class)}
    ):
        real_driver.initialize()
    assert real_driver.device is mock_device
    assert real_driver.initialized is True


def test_fail_initialization(real_driver: INA260Driver) -> None:
    """Test a failed initialization of a real sensor"""
    fake_ina260_class = MagicMock(side_effect=Exception("fail"))
    with patch.dict(
        "sys.modules", {"adafruit_ina260": MagicMock(INA260=fake_ina260_class)}
    ):
        with pytest.raises(SensorInitError):
            real_driver.initialize()
        assert real_driver.initialized is False


# ---------------------------------------------------------------------------------------
# Test read() method:

# Three branches:
#   - catch not initialized case
#   - sucessful reading
#   - failed reading


# Note, real driver is used as default because behavior does not branch if the
# sensor is sim or real
def test_catch_not_initialized(real_driver: INA260Driver) -> None:
    """Test the catch for not initialized sensor; can't read before initializing"""
    with pytest.raises(SensorReadError):
        real_driver.read()


def test_successful_reading(real_driver: INA260Driver) -> None:
    """Test a successful reading of the sensor"""
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.voltage = 12.8
    real_driver.device.current = 100
    real_driver.device.power = 1280
    results = real_driver.read()
    assert results[0].name == "voltage"
    assert results[0].value == 12.8
    assert results[0].unit == "V"
    assert results[1].name == "current"
    assert results[1].value == 100
    assert results[1].unit == "mA"
    assert results[2].name == "power"
    assert results[2].value == 100 * 12.8
    assert results[2].unit == "mW"


def test_failed_reading(real_driver: INA260Driver) -> None:
    """Test a successful reading of the sensor"""
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.voltage.return_value = 12.8
    real_driver.device.current.return_value = 100
    type(real_driver.device).power = PropertyMock(side_effect=Exception("fail"))
    with pytest.raises(SensorReadError):
        real_driver.read()


# ---------------------------------------------------------------------------------------
