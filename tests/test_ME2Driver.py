import pytest
from unittest.mock import patch, MagicMock
from src.ME2Driver import ME2Driver, FakeME2
from src.SensorExceptions import SensorInitError, SensorReadError

#------------------------------------------------------------------------------
# Setup
sensor_id   = "ME2"
i2c_bus     = None
fake_sensor = MagicMock()

readings_list = [{"name": "oxygen", 
                  "units": "percent", 
                  "min": 0, 
                   "max": 25}]
@pytest.fixture
def base_config():
    return {"sim": False,
            "IIC_mode": 0x01,
            "i2c_address": 0x73,
            "collection_number": 10,
            "readings": readings_list,
            "sim_fail_initialization": False
    }
@pytest.fixture
def sim_config(base_config):
     return {**base_config, "sim": True}

@pytest.fixture
def real_driver(base_config):
    return ME2Driver(sensor_id, base_config, i2c_bus, fake_sensor)

@pytest.fixture
def sim_driver(sim_config):
    return ME2Driver(sensor_id, sim_config, i2c_bus, fake_sensor)

#------------------------------------------------------------------------------
# Test initialize() method
def test_sim_initialize_success(sim_driver):
    sim_driver.initialize()
    assert sim_driver.initialized is True
    assert sim_driver.device is fake_sensor
        
def test_sim_initialize_failure(sim_driver):
    sim_driver.sim_fail_initialization = True 
    with pytest.raises(SensorInitError):
        sim_driver.initialize()
    assert sim_driver.initialized is False
    
def test_initialize_success(real_driver):
    mock_device = MagicMock()
    mock_IIC_class = MagicMock(return_value=mock_device)
    with patch.dict("sys.modules", {"DFRobot_Oxygen": 
        MagicMock(DFRobot_Oxygen_IIC=mock_IIC_class)}):
        real_driver.initialize()
        mock_IIC_class.assert_called_once_with(real_driver.IIC_mode, 
            real_driver.i2c_address)
        assert real_driver.initialized is True
        assert real_driver.device is mock_device
     
def test_initialize_failure(real_driver):
    mock_IIC_class = MagicMock(side_effect=Exception("fail"))
    with patch.dict("sys.modules", 
        {"DFRobot_Oxygen": MagicMock(DFRobot_Oxygen_IIC=mock_IIC_class)}):
        with pytest.raises(SensorInitError):
            real_driver.initialize()
        assert real_driver.initialized is False

#------------------------------------------------------------------------------
# Test read() method
def test_read_success(sim_driver):
    sim_driver.initialized = True
    sim_driver.device = MagicMock()
    sim_driver.device.get_oxygen_data.return_value = 20

    result = sim_driver.read()
    assert result[0].value == 20
    sim_driver.device.get_oxygen_data.assert_called_once_with(
        sim_driver.collection_number)
    
def test_read_failure(sim_driver):
    sim_driver.initialized = True
    sim_driver.device = MagicMock()
    sim_driver.device.get_oxygen_data.side_effect = Exception("fail")
    with pytest.raises(SensorReadError):
        sim_driver.read()
#------------------------------------------------------------------------------