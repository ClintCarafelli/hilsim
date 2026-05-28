import pytest
from unittest.mock import patch
from src.FakeSCD30 import FakeSCD30
from datetime import datetime, timedelta

#------------------------------------------------------------------------------
# Setup
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
def patch_time():
    return datetime(2024, 1, 1, 0, 0, 0)

@pytest.fixture
def SCD30():
    return FakeSCD30({"failure_rate": 0, "readings": reading_list})

#------------------------------------------------------------------------------
# Test get_measurement_interval() method
def test_FakeSCD30_set_measurement_interval(SCD30):
    SCD30.set_measurement_interval(2)
    assert SCD30.measurement_interval == 2

#------------------------------------------------------------------------------
# Test start_periodic_measurement() method
def test_FakeSCD30_start_periodic_measurement(SCD30, patch_time):
    with patch("src.FakeSCD30.datetime") as mock_dt:
        mock_dt.now.return_value = patch_time
        SCD30.start_periodic_measurement()
        assert SCD30.reading is True 
        assert SCD30.last_reading_time == patch_time

#------------------------------------------------------------------------------
# Test get_data_ready() method 
@pytest.mark.parametrize(
        "time_diff",
        [
            (1), 
            (2),
            (3),
        ]
)
def test_FakeSCD30_get_data_ready(SCD30, patch_time, time_diff):
    SCD30.measurement_interval = 2
    SCD30.last_reading_time = patch_time
    with patch("src.FakeSCD30.datetime") as mock_dt: 
        mock_dt.now.return_value = patch_time + timedelta(seconds=time_diff)
        result = SCD30.get_data_ready()
        if time_diff == 1: 
            assert result is False
        if time_diff == 2: 
            assert result is False
        if time_diff == 3: 
            assert result is True

#------------------------------------------------------------------------------
# Test read_measurement() method
def test_FakeSCD30_read_measurement_success(SCD30):
    with patch("src.FakeSCD30.random", return_value = 0.5): 
        result = SCD30.read_measurement()
        assert len(result) == 3
        assert result[0] == 20000
        assert result[1] == 47.5
        assert result[2] == 25
        assert len(result) == 3

# failure rate of 1 is always greater than random() which ensures failure
def test_FakeSCD30_read_measurement_fail(SCD30):
    SCD30.failure_rate = 1
    with pytest.raises(Exception):
         SCD30.read_measurement()

#------------------------------------------------------------------------------
# def test _in_range() method
def test_in_range(SCD30):
    with patch("src.FakeSCD30.random", return_value = 0.0):
        result = SCD30._in_range("CO2")
        assert result == 0.0
    with patch("src.FakeSCD30.random", return_value = 0.5):
        result = SCD30._in_range("CO2")
        assert result == 20000.0
    with patch("src.FakeSCD30.random", return_value = 1):
        result = SCD30._in_range("CO2")
        assert result == 40000.0
#------------------------------------------------------------------------------