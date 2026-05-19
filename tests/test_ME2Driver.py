import pytest
from unittest.mock import patch, MagicMock, call
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
def real_ME2Driver(base_config):
    return ME2Driver(sensor_id, base_config, i2c_bus)

@pytest.fixture
def sim_failure_ME2Driver(sim_failure_config):
    return ME2Driver(sensor_id, sim_failure_config, i2c_bus)

@pytest.fixture
def sim_success_ME2Driver(sim_success_config):
    return ME2Driver(sensor_id, sim_success_config, i2c_bus)

def test_sim_initialize(sim_success_ME2Driver):
    fake_device = MagicMock()
    with patch("src.ME2Driver.FakeME2", return_value=fake_device) as mock_FakeME2:
        sim_success_ME2Driver.initialize()
        assert sim_success_ME2Driver.initialized is True
        mock_FakeME2.assert_called_once_with(sim_success_ME2Driver.failure_rate,
                                              sim_success_ME2Driver.readings_meta_data)
        

def test_initialize_success(real_ME2Driver):
    mock_device = MagicMock()
    mock_IIC_class = MagicMock(return_value=mock_device)
    with patch.dict("sys.modules", {"DFRobot_Oxygen": MagicMock(DFRobot_Oxygen_IIC=mock_IIC_class)}):
        real_ME2Driver.initialize()

        mock_IIC_class.assert_called_once_with(real_ME2Driver.IIC_mode, real_ME2Driver.i2c_address)

        assert real_ME2Driver.initialized is True
        assert real_ME2Driver.device is mock_device
     
def test_initialize_failure(real_ME2Driver):
    mock_IIC_class = MagicMock(side_effect=Exception("fail"))
    with patch.dict("sys.modules", {"DFRobot_Oxygen": MagicMock(DFRobot_Oxygen_IIC=mock_IIC_class)}):
        with pytest.raises(SensorInitError):
            real_ME2Driver.initialize()
            mock_IIC_class.assert_called_once_with(real_ME2Driver.IIC_mode, real_ME2Driver.i2c_address)
            assert real_ME2Driver.initialized is True

def test_read_success(sim_success_ME2Driver):
    sim_success_ME2Driver.initialized = True
    sim_success_ME2Driver.device = MagicMock()
    sim_success_ME2Driver.device.get_oxygen_data.return_value = 20

    result = sim_success_ME2Driver.read()
    assert result[0].value == 20
    sim_success_ME2Driver.device.get_oxygen_data.assert_called_once_with(
        sim_success_ME2Driver.collection_number)
    
def test_read_failure(sim_success_ME2Driver):
    sim_success_ME2Driver.initialized = True
    sim_success_ME2Driver.device = MagicMock()
    sim_success_ME2Driver.device.get_oxygen_data.side_effect = Exception("fail")
    with pytest.raises(SensorReadError):
        sim_success_ME2Driver.read()
     
@patch("src.ME2Driver.random")
def test_get_oxygen_data(mock_random):
    FakeME2_instance = FakeME2(0,readings_list)
    mock_random.side_effect = [0.5, 0.5]
    result = FakeME2_instance.get_oxygen_data(10)
    assert result == 12.5





