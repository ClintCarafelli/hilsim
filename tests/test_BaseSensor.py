import pytest
from unittest.mock import patch, MagicMock
from src.BaseSensor import Reading, BaseSensor

@pytest.fixture
def example_reading():
    return Reading("CO2", 1200, "ppm")

def test_Reading_attributes(example_reading):
    assert example_reading.name  == "CO2"
    assert example_reading.value == 1200
    assert example_reading.unit  == "ppm"

def test_Reading_repr(example_reading):
    assert repr(example_reading) == "CO2: 1200 ppm"


readings_list = [{"name": "CO2",
            "units": "ppm",
            "min": 0,
            "max": 40000},
            {"name": "temp",
             "units": "C",
             "min": 0,
             "max": 65
            }]

nominal_config_dict = {"description": "sensor_description",
                       "readings": readings_list}

test_get_config_dict = {}

sensor_id = "SCD30"
i2c_bus   = None

class MockSensor(BaseSensor): 
    def initialize(self):
        self.initialized = True
    def read(self):
        return []
        
def test_BaseSensor_nominal_init():
    base_sensor = MockSensor(sensor_id, nominal_config_dict, i2c_bus)
    assert base_sensor.initialized is False
    assert base_sensor.description == "sensor_description"
    assert base_sensor.readings_meta_data == readings_list

def test_BaseSensor_no_description_or_readings_init():
    base_sensor = MockSensor(sensor_id, test_get_config_dict, i2c_bus)
    assert base_sensor.initialized is False
    assert base_sensor.description == sensor_id
    assert base_sensor.readings_meta_data == []

def test_BaseSensor_is_abstract():
    with pytest.raises(TypeError):
        BaseSensor(sensor_id, readings_list, i2c_bus)
