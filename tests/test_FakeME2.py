import pytest
from src.FakeME2 import FakeME2
from unittest.mock import patch

#------------------------------------------------------------------------------
# Setup
readings_list = [{"name": "oxygen", 
                  "units": "percent", 
                  "min": 0, 
                   "max": 25}]
@pytest.fixture
def success_config():
    return {"readings": readings_list, "failure_rate": 0}

@pytest.fixture
def failure_config():
    return {"readings": readings_list, "failure_rate": 1}

#------------------------------------------------------------------------------
# Test get_oxygen_data() method
def test_failure(failure_config):
    ME2 = FakeME2(failure_config)
    with pytest.raises(Exception):
        ME2.get_oxygen_data(10)

def test_success(success_config):
    ME2 = FakeME2(success_config)
    with patch("src.FakeME2.random", side_effect=[0.5, 0.5]) as mock_random: 
        result = ME2.get_oxygen_data(10) 
        assert result == 12.5
        assert mock_random.call_count == 2
#------------------------------------------------------------------------------
