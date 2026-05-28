import pytest
from src.FakeBMP388 import FakeBMP388
from unittest.mock import patch

#------------------------------------------------------------------------------
# Setup
readings_list= [{"name": "pressure", 
                 "units": "hpa", 
                 "min": 300, 
                 "max": 1250},
                {"name": "air_temp",
                 "units": "C",
                 "min": 0,
                 "max": 65}]

@pytest.fixture
def success_config(): 
    return {"readings": readings_list, "failure_rate": 0}

# self.get_same_random is a surrogate for random() which is always less than 1,
#  which gurantees failure
@pytest.fixture
def failure_config(): 
    return {"readings": readings_list, "failure_rate": 1}

@pytest.fixture
def success_sensor(success_config):
    return FakeBMP388(success_config)

@pytest.fixture
def fail_sensor(failure_config):
    return  FakeBMP388(failure_config)

#------------------------------------------------------------------------------
# Test _get_same_random() method
def test_get_same_random(success_sensor): 
    with patch("src.FakeBMP388.random", return_value=0.1):
        success_sensor._get_same_random()
        assert success_sensor.rand_num == 0.5
        assert success_sensor.counter == 1
        success_sensor._get_same_random()
        assert success_sensor.rand_num == 0.1
        assert success_sensor.counter == 2

#------------------------------------------------------------------------------
# Test pressure property
def test_pressure_success(success_sensor): 
    with patch("src.FakeBMP388.random", return_value=0.5):
        assert success_sensor.pressure == 775

def test_pressure_fail(fail_sensor): 
    with pytest.raises(Exception):
        fail_sensor.pressure

#------------------------------------------------------------------------------
# Test temperature property
def test_temperature_success(success_sensor): 
    with patch("src.FakeBMP388.random", return_value=0.5):
        assert success_sensor.temperature == 32.5

def test_temperature_fail(fail_sensor): 
    with pytest.raises(Exception):
        fail_sensor.temperature
#------------------------------------------------------------------------------










