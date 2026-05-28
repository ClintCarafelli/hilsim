import pytest
from src.FakeSTEMMA import FakeSTEMMA
from unittest.mock import patch, MagicMock

#------------------------------------------------------------------------------
# Setup
readings = [{"name": "moisture",
             "units": "None",
             "max": 2000,
             "min": 200},
             {"name": "temp",
              "units": "C",
              "max": 85,
              "min": -40}]

@pytest.fixture
def config():
    return {"readings": readings, "failure_rate": 0}

@pytest.fixture
def fake_sensor(config):
    return FakeSTEMMA(config)

#------------------------------------------------------------------------------
# Test moisture_read() method
def test_moisture_read_success(fake_sensor):
    with patch.object(fake_sensor, "_in_range", return_value=10):
        result = fake_sensor.moisture_read()
        assert result == 10

def test_moisture_read_fail(fake_sensor):
    fake_sensor.failure_rate =  1
    with pytest.raises(Exception):
        fake_sensor.moisture_read()

#------------------------------------------------------------------------------
# Test get_temp() method
def test_temp_read_success(fake_sensor):
    with patch.object(fake_sensor, "_in_range", return_value=9):
        result = fake_sensor.get_temp()
        assert result == 9

def test_temp_read_fail(fake_sensor):
    fake_sensor.failure_rate =  1
    with pytest.raises(Exception):
        fake_sensor.get_temp()

#------------------------------------------------------------------------------
# Test _in_range() method
def test_in_range(fake_sensor):
    with patch("src.FakeSTEMMA.random", return_value = 0.0):
        result = fake_sensor._in_range("moisture")
        assert result == 200.0
    with patch("src.FakeSTEMMA.random", return_value = 0.5):
        result = fake_sensor._in_range("moisture")
        assert result == 1100.0
    with patch("src.FakeSTEMMA.random", return_value = 1):
        result = fake_sensor._in_range("moisture")
        assert result == 2000.0

def test_get_same_random(fake_sensor): 
    with patch("src.FakeSTEMMA.random", return_value=0.1):
        fake_sensor._get_same_random()
        assert fake_sensor.rand_num == 0
        assert fake_sensor.counter  == 1
        fake_sensor._get_same_random()
        assert fake_sensor.rand_num == 0.1
        assert fake_sensor.counter  == 2
#------------------------------------------------------------------------------