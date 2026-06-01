""" Test the fake_me2 sensor that does not require hardware"""

from unittest.mock import patch
import pytest
from src.fake_me2 import FakeME2


# ------------------------------------------------------------------------------
# Setup
READINGS_LIST = [{"name": "oxygen", "units": "percent", "min": 0, "max": 25}]


@pytest.fixture
def success_config() -> dict:
    """create config dict that does not fail"""
    return {"readings": READINGS_LIST, "failure_rate": 0}


@pytest.fixture
def failure_config() -> dict:
    """create config dict that gurantees failure"""
    return {"readings": READINGS_LIST, "failure_rate": 1}


# ------------------------------------------------------------------------------
# Test get_oxygen_data() method

# Two branches: 
#    - fail to return a value
#    - successfully return a value


def test_failure(failure_config: dict) -> None:
    """Test failed value production"""
    me2 = FakeME2(failure_config)
    with pytest.raises(ValueError):
        me2.get_oxygen_data(10)


def test_success(success_config: dict) -> None:
    """Test successful value production"""
    me2 = FakeME2(success_config)
    se_list = [0.5] * 11
    with patch("src.fake_me2.random", side_effect=se_list) as mock_random:
        result = me2.get_oxygen_data(10)
        assert result == 12.5
        assert mock_random.call_count == 11


# ------------------------------------------------------------------------------
# Test check_collection_number() method:

# Two branches: 
#    - collection number is too low (raises ValueError)
#    - collection number is fine (doe nothing)

def test_check_collection_number_low(success_config: dict) -> None:
    """Test to make sure method raises ValueError"""
    me2 = FakeME2(success_config)
    with pytest.raises(ValueError):
        me2.check_collection_number(1)


def test_check_collection_number_high(success_config: dict) -> None:
    """Test to make sure method raises ValueError"""
    me2 = FakeME2(success_config)
    me2.check_collection_number(10)


# ------------------------------------------------------------------------------
