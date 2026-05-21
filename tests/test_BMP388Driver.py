import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from src.BMP388Driver import BMP388Driver, FakeBMP388
from src.SensorExceptions import SensorInitError, SensorReadError

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
def sim_success_config(base_config):
    return {**base_config, "sim": True}

@pytest.fixture
def sim_failure_config(base_config):
    return {**base_config, "sim": True, "failure_rate": 1}

@pytest.fixture
def real_BMP388Driver(base_config):
    return BMP388Driver(sensor_id, base_config, i2c_bus)

@pytest.fixture
def sim_success_BMP388Driver(sim_success_config):
    return BMP388Driver(sensor_id, sim_success_config, i2c_bus)

@pytest.fixture
def sim_success_BMP388Driver(sim_failure_config):
    return BMP388Driver(sensor_id, sim_failure_config, i2c_bus)

def test_sim_initialize(sim_success_BMP388Driver):
    fake_driver = MagicMock()
    with patch("src.BMP388Driver.FakeBMP388",return_value=fake_driver) as mock_FakeBMP388: 
        sim_success_BMP388Driver.initialize()
        assert sim_success_BMP388Driver.device is fake_driver
        assert sim_success_BMP388Driver.initialized is True
        mock_FakeBMP388.assert_called_once_with(
            sim_success_BMP388Driver.failure_rate, 
            sim_success_BMP388Driver.readings_meta_data)

def test_initialize_success(real_BMP388Driver):
    mock_device = MagicMock()
    mock_BMP3XX_I2C_class = MagicMock(return_value=mock_device)
    with patch.dict("sys.modules", {"adafruit_bmp3xx": MagicMock(BMP3XX_I2C=mock_BMP3XX_I2C_class)}):
        real_BMP388Driver.initialize()
        assert real_BMP388Driver.initialized is True
        assert real_BMP388Driver.device is mock_device
        mock_BMP3XX_I2C_class.assert_called_once_with(
            real_BMP388Driver.i2c_bus)

def test_initialize_failure(real_BMP388Driver):
    mock_device = MagicMock()
    mock_BMP3XX_I2C_class = MagicMock(side_effect=Exception("fail"))
    with patch.dict("sys.modules", {"adafruite_bmp3xx": MagicMock(BM3XX_I2C=mock_BMP3XX_I2C_class)}):
        with pytest.raises(SensorInitError):
            real_BMP388Driver.initialize()
            assert real_BMP388Driver.device is mock_device
            mock_BMP3XX_I2C_class.assert_called_once_with(
                real_BMP388Driver.i2c_bus)
            assert real_BMP388Driver.initialized is False
        
def test_read_not_initialized(real_BMP388Driver):
    with pytest.raises(SensorReadError):
        real_BMP388Driver.read()


def test_read_success(real_BMP388Driver):
    real_BMP388Driver.initialized        = True
    real_BMP388Driver.device             = MagicMock()
    real_BMP388Driver.device.pressure    = 1
    real_BMP388Driver.device.temperature = 2

    result = real_BMP388Driver.read()
    print(result)
    assert result[0].value == 1
    assert result[1].value == 2

def test_read_failure(real_BMP388Driver):
    real_BMP388Driver.initialized = True
    real_BMP388Driver.device = MagicMock()
    type(real_BMP388Driver.device).pressure = PropertyMock(side_effect=Exception("fail"))
    with pytest.raises(SensorReadError):
        result = real_BMP388Driver.read() 
        assert result[0].value is None
        assert result[1].value is None

@pytest.fixture
def success_FAKEBMP388():
    with patch("src.BMP388Driver.random", return_value=0.5):
        val_creator =  FakeBMP388(0, readings_list)
        assert val_creator.rand_num == 0.5
        return val_creator 

@pytest.fixture
def fail_FAKEBMP388():
     with patch("src.BMP388Driver.random", return_value=0.5):
        val_creator =  FakeBMP388(1, readings_list)
        assert val_creator.rand_num == 0.5
        return val_creator 

def test_success_FAKEBMP388(success_FAKEBMP388):
    with patch("src.BMP388Driver.random", return_value=0.5):
        assert success_FAKEBMP388.pressure == 775
        assert success_FAKEBMP388.temperature == 32.5

def test_success_FAKEBMP388(fail_FAKEBMP388):
    with patch("src.BMP388Driver.random", return_value=0.5):
        assert fail_FAKEBMP388.pressure is None
        assert fail_FAKEBMP388.temperature is None















