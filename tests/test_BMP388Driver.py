import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from src.BMP388Driver import BMP388Driver, FakeBMP388
from src.SensorExceptions import SensorInitError, SensorReadError
from random import random

sensor_id = "BMP388"
i2c_bus = None

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
            "readings": readings_list}

@pytest.fixture
def sim_config(base_config):
    return {**base_config, "sim": True}

@pytest.fixture
def real_driver(base_config):
    return BMP388Driver(sensor_id, base_config, i2c_bus)

@pytest.fixture
def sim_driver(sim_config):
    return BMP388Driver(sensor_id, sim_config, i2c_bus)

def test_sim_initialize_success(sim_driver):
    fake_driver = MagicMock()
    with patch("src.BMP388Driver.FakeBMP388",return_value=fake_driver) as mock_FakeBMP388: 
        sim_driver.initialize()
        assert sim_driver.device is fake_driver
        assert sim_driver.initialized is True
        mock_FakeBMP388.assert_called_once_with(
            sim_driver.failure_rate, 
            sim_driver.readings_meta_data)
        
def test_sim_initialize_failure(sim_driver):
    with patch("src.BMP388Driver.FakeBMP388", side_effect=Exception("fail")):
        with pytest.raises(SensorInitError):
            sim_driver.initialize()
        assert sim_driver.initialized is False
    
def test_initialize_success(real_driver):
    mock_device = MagicMock()
    mock_BMP3XX_I2C_class = MagicMock(return_value=mock_device)
    with patch.dict("sys.modules", {"adafruit_bmp3xx": MagicMock(BMP3XX_I2C=mock_BMP3XX_I2C_class)}):
        real_driver.initialize()
        assert real_driver.initialized is True
        assert real_driver.device is mock_device
        mock_BMP3XX_I2C_class.assert_called_once_with(
            real_driver.i2c_bus)

def test_initialize_failure(real_driver):
    mock_BMP3XX_I2C_class = MagicMock(side_effect=Exception("fail"))
    with patch.dict("sys.modules", {"adafruit_bmp3xx": MagicMock(BMP3XX_I2C=mock_BMP3XX_I2C_class)}):
        with pytest.raises(SensorInitError):
            real_driver.initialize()
        assert real_driver.initialized is False
        
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
    type(real_driver.device).pressure = PropertyMock(side_effect=Exception("fail"))
    with pytest.raises(SensorReadError):
        result = real_driver.read()

@pytest.fixture
def success_fake_driver():
    return  FakeBMP388(0, readings_list)

@pytest.fixture
def fail_fake_driver():
    # self.get_same_random is a surrogate for random() which is always less than 1, which gurantees failure
    return  FakeBMP388(1, readings_list)

def test_get_same_random(success_fake_driver): 
    with patch("src.BMP388Driver.random", return_value=0.1):
        success_fake_driver._get_same_random()
        assert success_fake_driver.rand_num == 0.5
        assert success_fake_driver.counter == 1
        success_fake_driver._get_same_random()
        assert success_fake_driver.rand_num == 0.1
        assert success_fake_driver.counter == 2

def test_pressure_success(success_fake_driver): 
    with patch("src.BMP388Driver.random", return_value=0.5):
        assert success_fake_driver.pressure == 775

def test_pressure_fail(fail_fake_driver): 
    with pytest.raises(Exception):
        fail_fake_driver.pressure

def test_temperature_success(success_fake_driver): 
    with patch("src.BMP388Driver.random", return_value=0.5):
        assert success_fake_driver.temperature == 32.5

def test_temperature_fail(fail_fake_driver): 
    with pytest.raises(Exception):
        fail_fake_driver.temperature












