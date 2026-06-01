"""Tests for the ME2 Driver"""

from unittest.mock import MagicMock, patch

import pytest
from src.me2_driver import ME2Driver
from src.SensorExceptions import SensorInitError, SensorReadError

# ------------------------------------------------------------------------------
# Setup
SENSOR_ID = "ME2"
I2C_BUS = None
FAKE_SENSOR = MagicMock()
READINGS_LIST = [{"name": "oxygen", "units": "percent", "min": 0, "max": 25}]


@pytest.fixture
def base_config() -> dict:
    """Set up the basic config"""
    return {
        "sim": False,
        "IIC_mode": 0x01,
        "i2c_address": 0x73,
        "collection_number": 10,
        "readings": READINGS_LIST,
        "sim_fail_initialization": False,
    }


@pytest.fixture
def sim_config(base_config: dict) -> dict:
    """Set up the sim config"""
    return {**base_config, "sim": True}


@pytest.fixture
def real_driver(base_config: dict) -> ME2Driver:
    """Create an instance of a driver with real sensor paths"""
    return ME2Driver(SENSOR_ID, base_config, I2C_BUS, FAKE_SENSOR)


@pytest.fixture
def sim_driver(sim_config: dict) -> ME2Driver:
    """Create an instance of a driver with sim sensor paths"""
    return ME2Driver(SENSOR_ID, sim_config, I2C_BUS, FAKE_SENSOR)


# ------------------------------------------------------------------------------
# Test initialize() method

# Four Branches:
#    - Sim Sensor:
#        - initialization success
#        - initialization failure
#    - Real sensor:
#        - initialization success
#        - initialization failure


def test_sim_initialize_success(sim_driver: ME2Driver):
    """Test sim sensor initilization success"""
    sim_driver.initialize()
    assert sim_driver.initialized is True
    assert sim_driver.device is FAKE_SENSOR


def test_sim_initialize_failure(sim_driver: ME2Driver) -> None:
    """Test sim sensor initilization failure"""
    sim_driver.sim_fail_initialization = True
    with pytest.raises(SensorInitError):
        sim_driver.initialize()
    assert sim_driver.initialized is False


def test_initialize_success(real_driver: ME2Driver) -> None:
    """Test real sensor initialization success"""
    mock_device = MagicMock()
    mock_IIC_class = MagicMock(return_value=mock_device)
    with patch.dict(
        "sys.modules", {"DFRobot_Oxygen": MagicMock(DFRobot_Oxygen_IIC=mock_IIC_class)}
    ):
        real_driver.initialize()
        mock_IIC_class.assert_called_once_with(
            real_driver.iic_mode, real_driver.i2c_address
        )
        assert real_driver.initialized is True
        assert real_driver.device is mock_device


def test_initialize_failure(real_driver: ME2Driver) -> None:
    """Test real sensor initialization failure"""
    mock_IIC_class = MagicMock(side_effect=Exception("fail"))
    with patch.dict(
        "sys.modules", {"DFRobot_Oxygen": MagicMock(DFRobot_Oxygen_IIC=mock_IIC_class)}
    ):
        with pytest.raises(SensorInitError):
            real_driver.initialize()
        assert real_driver.initialized is False


# ------------------------------------------------------------------------------
# Test read() method

# Two branches:
#   - successful reading
#   - failed reading


def test_read_success(sim_driver: ME2Driver) -> None:
    """Test a successful reading"""
    sim_driver.initialized = True
    sim_driver.device = MagicMock()
    sim_driver.device.get_oxygen_data.return_value = 20

    result = sim_driver.read()
    assert result[0].value == 20
    sim_driver.device.get_oxygen_data.assert_called_once_with(
        sim_driver.collection_number
    )


def test_read_failure(sim_driver: ME2Driver) -> None:
    """Test a failed reading"""
    sim_driver.initialized = True
    sim_driver.device = MagicMock()
    sim_driver.device.get_oxygen_data.side_effect = Exception("fail")
    with pytest.raises(SensorReadError):
        sim_driver.read()


# ------------------------------------------------------------------------------
