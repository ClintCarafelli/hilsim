import pytest
from unittest.mock import patch, MagicMock
from src.ME2Driver import ME2Driver, FakeME2
from src.SensorExceptions import SensorInitError, SensorReadError

sensor_id = "ME2"
i2c_bus = None

readings_list = [{"name": "oxygen", 
                  "units": "percent", 
                  "min": 0, 
                   "max": 25}]
@pytest.fixture
def base_config():
    return {"sim": False, 
            "failure_rate": 0,
            "IIC_mode": 0x01,
            "i2c_address": 0x73,
            "collection_number": 10,
            "readings": readings_list
    }
@pytest.fixture
def sim_failure_config(base_config):
     return {**base_config, "sim": True, "failure_rate": 1}

@pytest.fixture
def sim_success_config(base_config):
     return {**base_config, "sim": True, "failure_rate": 0}

@pytest.fixture
def real_driver(base_config):
    return ME2Driver(sensor_id, base_config, i2c_bus)

@pytest.fixture
def sim_driver(sim_success_config):
    return ME2Driver(sensor_id, sim_success_config, i2c_bus)

def test_sim_initialize_success(sim_driver):
    fake_device = MagicMock()
    with patch("src.ME2Driver.FakeME2") as mock_FakeME2:
        sim_driver.initialize()
        assert sim_driver.initialized is True
        mock_FakeME2.assert_called_once_with(sim_driver.failure_rate,
                                              sim_driver.readings_meta_data)
        
def test_sim_initialize_fail(sim_driver):
    with patch("src.ME2Driver.FakeME2", side_effect=Exception("fail")):
        with pytest.raises(SensorInitError):
            sim_driver.initialize()
    
def test_initialize_success(real_driver):
    mock_device = MagicMock()
    mock_IIC_class = MagicMock(return_value=mock_device)
    with patch.dict("sys.modules", {"DFRobot_Oxygen": MagicMock(DFRobot_Oxygen_IIC=mock_IIC_class)}):
        real_driver.initialize()

        mock_IIC_class.assert_called_once_with(real_driver.IIC_mode, real_driver.i2c_address)

        assert real_driver.initialized is True
        assert real_driver.device is mock_device
     
def test_initialize_failure(real_driver):
    mock_IIC_class = MagicMock(side_effect=Exception("fail"))
    with patch.dict("sys.modules", {"DFRobot_Oxygen": MagicMock(DFRobot_Oxygen_IIC=mock_IIC_class)}):
        with pytest.raises(SensorInitError):
            real_driver.initialize()
        assert real_driver.initialized is False

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

def test_simulated_reading_failure():
    ME2 = FakeME2(1, readings_list)
    with pytest.raises(Exception):
        ME2.get_oxygen_data(10)

def test_get_oxygen_data_success():
    ME2 = FakeME2(0, readings_list)
    with patch("src.ME2Driver.random", side_effect=[0.5, 0.5]) as mock_random: 
        result = ME2.get_oxygen_data(10) 
        assert result == 12.5
        assert mock_random.call_count == 2
