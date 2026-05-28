import pytest
from unittest.mock import patch, MagicMock
from src.SCD30Driver import SCD30Driver
from src.SensorExceptions import SensorInitError, SensorReadError

#------------------------------------------------------------------------------
# Setup
sensor_id    = "SCD30"
i2c_bus      = None 
fake_sensor  = MagicMock()
reading_list = [{"name": "CO2",
                 "units": "ppm",
                 "min": 0,
                 "max": 40000,
                 },
                 {"name": "relative_humidity",
                 "units": "percent",
                 "min": 0,
                 "max": 95,
                 },
                 {"name": "temp",
                 "units": "C",
                 "min": 0,
                 "max": 50,
                 }]

@pytest.fixture
def base_config():
    return {"readings": reading_list, 
            "sim": False, 
            "sim_fail_initialization": False}

@pytest.fixture
def sim_config(base_config):
    return {**base_config, "sim":True}

@pytest.fixture
def sim_driver(sim_config):
    return SCD30Driver(sensor_id, sim_config, i2c_bus, fake_sensor)

@pytest.fixture
def real_driver(base_config):
    return SCD30Driver(sensor_id, base_config, i2c_bus, fake_sensor)

#------------------------------------------------------------------------------
# Test initialize() method 
def test_sim_initialization_success(sim_driver):
        sim_driver.initialize()
        assert sim_driver.device is fake_sensor
        assert sim_driver.initialized is True
        sim_driver.device.set_measurement_interval.assert_called_once_with(2)
        sim_driver.device.start_periodic_measurement.assert_called_once_with()

def test_sim_initialization_failure(sim_driver):
    sim_driver.sim_fail_initialization = True
    with pytest.raises(SensorInitError):
        sim_driver.initialize()
    assert sim_driver.initialized is False
    assert sim_driver.device is None

def test_real_initialization_success(real_driver):
    mock_device = MagicMock()
    fake_SCD30_class = MagicMock(return_value=mock_device)
    with patch.dict("sys.modules", {"scd30_i2c": 
        MagicMock(SCD30=fake_SCD30_class)}):
        real_driver.initialize()
        assert real_driver.device is mock_device
        assert real_driver.initialized is True
        real_driver.device.set_measurement_interval.assert_called_once_with(2)
        real_driver.device.start_periodic_measurement.assert_called_once_with()

def test_real_initialization_failure(real_driver):
    fake_SCD30_class = MagicMock(side_effect=Exception("fail"))
    with patch.dict("sys.modules", {"scd30_i2c": 
        MagicMock(SCD30=fake_SCD30_class)}):
        with pytest.raises(SensorInitError):
            real_driver.initialize()
        assert real_driver.initialized is False

#------------------------------------------------------------------------------
# Test read() method 
def test_read_not_initialized(real_driver):
    with pytest.raises(SensorReadError):
        real_driver.read()

def test_read_success(real_driver):
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.read_measurement.return_value = [1,2,3]
    result = real_driver.read()
    assert result[0].value == 1
    assert result[1].value == 2
    assert result[2].value == 3
    assert len(result) == 3

def test_read_failure(real_driver):
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.read_measurement.side_effect = Exception("fail")
    with pytest.raises(SensorReadError):
        result = real_driver.read()
#------------------------------------------------------------------------------