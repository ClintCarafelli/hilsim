import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from src.BMP388Driver import BMP388Driver, FakeBMP388
from src.SensorExceptions import SensorInitError, SensorReadError
from random import random

#------------------------------------------------------------------------------
# Setup
sensor_id   = "BMP388"
i2c_bus     = None
fake_sensor = MagicMock()

readings_list= [{"name": "pressure", 
                 "units": "hpa", 
                 "min": 300, 
                 "max": 1250},
                {"name": "air_temp",
                 "units": "C",
                 "min": 0,
                 "max": 65}]

@pytest.fixture
def base_config():
    return {"sim": False,
            "failure_rate": 0,
            "readings": readings_list,
            "sim_fail_initialization": False}

@pytest.fixture
def sim_config(base_config):
    return {**base_config, "sim": True}

@pytest.fixture
def real_driver(base_config):
    return BMP388Driver(sensor_id, base_config, i2c_bus, fake_sensor)

@pytest.fixture
def sim_driver(sim_config):
    return BMP388Driver(sensor_id, sim_config, i2c_bus, fake_sensor)

#------------------------------------------------------------------------------
# Test init
def test_real_setup(real_driver):
    assert real_driver.sim is False
    assert real_driver.device is None

def test_sim_setup(sim_driver):
    assert sim_driver.sim is True
    assert sim_driver.device is None
    assert sim_driver.fake_sensor is fake_sensor
    assert sim_driver.sim_fail_initialization is False
    
#------------------------------------------------------------------------------
# Test initialize() method
def test_sim_initialize_success(sim_driver):
    sim_driver.initialize()
    assert sim_driver.device is fake_sensor
    assert sim_driver.initialized is True
        
def test_sim_initialize_failure(sim_driver):
    sim_driver.sim_fail_initialization = True
    with pytest.raises(SensorInitError):
        sim_driver.initialize()
    assert sim_driver.initialized is False
    
def test_initialize_success(real_driver):
    mock_device = MagicMock()
    mock_BMP3XX_I2C_class = MagicMock(return_value=mock_device)
    with patch.dict("sys.modules", {"adafruit_bmp3xx": 
        MagicMock(BMP3XX_I2C=mock_BMP3XX_I2C_class)}):
        real_driver.initialize()
        assert real_driver.initialized is True
        assert real_driver.device is mock_device
        mock_BMP3XX_I2C_class.assert_called_once_with(real_driver.i2c_bus)

def test_initialize_failure(real_driver):
    mock_BMP3XX_I2C_class = MagicMock(side_effect=Exception("fail"))
    with patch.dict("sys.modules", {"adafruit_bmp3xx": 
        MagicMock(BMP3XX_I2C=mock_BMP3XX_I2C_class)}):
        with pytest.raises(SensorInitError):
            real_driver.initialize()
        assert real_driver.initialized is False
        
#------------------------------------------------------------------------------
# Test read() method
def test_read_not_initialized(real_driver):
    with pytest.raises(SensorReadError):
        real_driver.read()

def test_read_success(real_driver):
    real_driver.initialized        = True
    real_driver.device             = MagicMock()
    real_driver.device.pressure    = 1
    real_driver.device.temperature = 2

    result = real_driver.read()
    assert result[0].value == 1
    assert result[1].value == 2

def test_read_failure(real_driver):
    real_driver.initialized = True
    real_driver.device = MagicMock()
    type(real_driver.device).pressure = PropertyMock(side_effect=
        Exception("fail"))
    with pytest.raises(SensorReadError):
        result = real_driver.read()
#------------------------------------------------------------------------------
