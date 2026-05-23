import pytest
from unittest.mock import patch, MagicMock
from src.STEMMADriver import STEMMADriver, FakeSTEMMA
from src.SensorExceptions import SensorInitError, SensorReadError

sensor_id   = "STEMMA"
i2c_bus     = None
i2c_address = 0x36

readings = [{"name": "moisture",
             "units": "None",
             "max": 2000,
             "min": 200},
             {"name": "temp",
              "units": "C",
              "max": 85,
              "min": -40}]

@pytest.fixture
def base_config():
    return {"sim": False,
            "failure_rate": 0,
            "i2c_address": i2c_address,
            "readings": readings}

@pytest.fixture
def sim_success_config(base_config):
    return {**base_config, "sim": True}

@pytest.fixture
def sim_driver(sim_success_config):
    return STEMMADriver(sensor_id, sim_success_config, i2c_bus)

@pytest.fixture
def real_driver(base_config):
    return STEMMADriver(sensor_id, base_config, i2c_bus)


def test_sim_initialize_success(sim_driver):
    fake_device = MagicMock()
    with patch("src.STEMMADriver.FakeSTEMMA", return_value=fake_device) as mock_STEMMA:
        sim_driver.initialize()
        assert sim_driver.initialized is True
        assert sim_driver.device is fake_device
        mock_STEMMA.assert_called_once_with(sim_driver.failure_rate, 
                                            sim_driver.readings_meta_data)
        
def test_sim_initialize_fail(sim_driver):
      with patch("src.STEMMADriver.FakeSTEMMA", side_effect=Exception("fail")):
          with pytest.raises(SensorInitError):
              sim_driver.initialize()


def test_real_initialize(real_driver):
    mock_seesaw = MagicMock()
    with patch.dict("sys.modules", { "adafruit_seesaw": MagicMock(),
        "adafruit_seesaw.seesaw": MagicMock(Seesaw=mock_seesaw)
    }):
        real_driver.initialize()
        assert real_driver.initialized is True

def test_read_not_init_failure(real_driver):
    with pytest.raises(SensorReadError):
        real_driver.read()

def test_read_success(real_driver):
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.moisture_read.return_value = 1000
    real_driver.device.get_temp.return_value = 30
    result = real_driver.read()
    assert len(result) == 2
    assert result[0].value == 1000
    assert result[1].value == 30

def test_read_failure(real_driver):
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.moisture_read.side_effect=Exception("fail")
    with pytest.raises(SensorReadError):
        real_driver.read()

@pytest.fixture
def fake_sensor():
    return FakeSTEMMA(0, readings)

def test_moisture_read_success(fake_sensor):
    with patch.object(fake_sensor, "_in_range", return_value=10):
        result = fake_sensor.moisture_read()
        assert result == 10

def test_moisture_read_fail(fake_sensor):
    fake_sensor.failure_rate =  1
    with pytest.raises(Exception):
        fake_sensor.moisture_read()

def test_temp_read_success(fake_sensor):
    with patch.object(fake_sensor, "_in_range", return_value=9):
        result = fake_sensor.get_temp()
        assert result == 9

def test_temp_read_fail(fake_sensor):
    fake_sensor.failure_rate =  1
    with pytest.raises(Exception):
        fake_sensor.get_temp()

def test_in_range(fake_sensor):
    with patch("src.STEMMADriver.random", return_value = 0.0):
        result = fake_sensor._in_range("moisture")
        assert result == 200.0
    with patch("src.STEMMADriver.random", return_value = 0.5):
        result = fake_sensor._in_range("moisture")
        assert result == 1100.0
    with patch("src.STEMMADriver.random", return_value = 1):
        result = fake_sensor._in_range("moisture")
        assert result == 2000.0

def test_get_same_random(fake_sensor): 
    with patch("src.STEMMADriver.random", return_value=0.1):
        fake_sensor._get_same_random()
        assert fake_sensor.rand_num == 0.5
        assert fake_sensor.counter == 1
        fake_sensor._get_same_random()
        assert fake_sensor.rand_num == 0.1
        assert fake_sensor.counter == 2
    







