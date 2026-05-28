import pytest
from unittest.mock import patch, MagicMock
from src.STEMMADriver import STEMMADriver, FakeSTEMMA
from src.SensorExceptions import SensorInitError, SensorReadError

#------------------------------------------------------------------------------
# Setup
sensor_id   = "STEMMA"
i2c_bus     = None
i2c_address = 0x36
fake_sensor = MagicMock()

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
            "i2c_address": i2c_address,
            "readings": readings,
            "sim_fail_initialization": False}

@pytest.fixture
def success_config(base_config):
    return {**base_config, "sim": True}

@pytest.fixture
def sim_driver(success_config):
    return STEMMADriver(sensor_id, success_config, i2c_bus, fake_sensor)

@pytest.fixture
def real_driver(base_config):
    return STEMMADriver(sensor_id, base_config, i2c_bus, fake_sensor)

#------------------------------------------------------------------------------
# Test initialize() method
def test_sim_initialize_success(sim_driver):
    sim_driver.initialize()
    assert sim_driver.initialized is True
    assert sim_driver.device is fake_sensor
        
def test_sim_initialize_fail(sim_driver):
    sim_driver.sim_fail_initialization = True
    with pytest.raises(SensorInitError):
        sim_driver.initialize()
    assert sim_driver.initialized is False
    assert sim_driver.device is None

def test_real_initialize(real_driver):
    mock_seesaw = MagicMock()
    with patch.dict("sys.modules", { "adafruit_seesaw": MagicMock(),
        "adafruit_seesaw.seesaw": MagicMock(Seesaw=mock_seesaw)
    }):
        real_driver.initialize()
        assert real_driver.initialized is True

#------------------------------------------------------------------------------
# Test read() method
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
#------------------------------------------------------------------------------