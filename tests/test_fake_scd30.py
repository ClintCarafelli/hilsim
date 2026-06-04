"""Test the fake SCD30"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from src.scd30 import FakeSCD30

# ------------------------------------------------------------------------------
# Setup
READING_LIST = [
    {
        "name": "CO2",
        "units": "ppm",
        "min": 0,
        "max": 40000,
    },
    {
        "name": "relative_humidity",
        "units": "percent",
        "min": 0,
        "max": 95,
    },
    {
        "name": "temp",
        "units": "C",
        "min": 0,
        "max": 50,
    },
]


@pytest.fixture
def patch_time() -> datetime:
    """Create a standard time to use a reference for measurement intervals"""
    return datetime(2024, 1, 1, 0, 0, 0)


@pytest.fixture
def scd30() -> FakeSCD30:
    """Create an instance of the FakeSCD30"""
    return FakeSCD30({"failure_rate": 0, "readings": READING_LIST})


# ------------------------------------------------------------------------------
# Test get_measurement_interval() method


# No branches, but make sure measurement interval is set, which get_data_ready
# depends on
def test_set_measurement_interval(scd30: FakeSCD30) -> None:
    """Test measurement interval gets set"""
    scd30.set_measurement_interval(2)
    assert scd30.measurement_interval == 2


# ------------------------------------------------------------------------------
# Test start_periodic_measurement() method

# No branches, but ensure last reading time is set. Mostly implimented to
# mirror actual driver code


def test_start_periodic_measurement(scd30: FakeSCD30, patch_time: datetime) -> None:
    """Test the start_periodic_measurement is set"""
    with patch("src.scd30.datetime") as mock_dt:
        mock_dt.now.return_value = patch_time
        scd30.start_periodic_measurement()
        assert scd30.reading is True
        assert scd30.last_reading_time == patch_time


# ------------------------------------------------------------------------------
# Test get_data_ready() method

# Three Branches:
#    - current time elapsed is less than measurement_interval, data is not ready
#    - current time elapsed is equal to than measurement_interval, data is not ready
#    - current time elapsed is greater than measurement_interval, data is ready


@pytest.mark.parametrize(
    "time_diff",
    [
        (1),
        (2),
        (3),
    ],
)
def test_get_data_ready(scd30: FakeSCD30, patch_time: datetime, time_diff: int) -> None:
    """Test get data ready over all three time elapsed cases"""
    scd30.measurement_interval = 2
    scd30.last_reading_time = patch_time
    with patch("src.scd30.datetime") as mock_dt:
        mock_dt.now.return_value = patch_time + timedelta(seconds=time_diff)
        result = scd30.get_data_ready()
        if time_diff == 1:
            assert result is False
        if time_diff == 2:
            assert result is False
        if time_diff == 3:
            assert result is True


# ------------------------------------------------------------------------------
# Test read_measurement() method

# Two branches
#    - successful reading (returns values)
#    - failed reading (raises Exception)


def test_read_measurement_success(scd30: FakeSCD30) -> None:
    """Test a successful reading"""
    with patch("src.scd30.random", return_value=0.5):
        result = scd30.read_measurement()
        assert len(result) == 3
        assert result[0] == 20000
        assert result[1] == 47.5
        assert result[2] == 25
        assert len(result) == 3


# failure rate of 1 is always greater than random() which ensures failure
def test_read_measurement_fail(scd30: FakeSCD30) -> None:
    """Test a failed reading"""
    scd30.failure_rate = 1
    with pytest.raises(Exception):
        scd30.read_measurement()


# ------------------------------------------------------------------------------
# def test _in_range() method

# No branches, but check edges cases produced by random() and a middle case


def test_in_range(scd30: FakeSCD30) -> None:
    """Test that in_range generates expected values"""
    with patch("src.scd30.random", return_value=0.0):
        result = scd30._in_range("CO2")
        assert result == 0.0
    with patch("src.scd30.random", return_value=0.5):
        result = scd30._in_range("CO2")
        assert result == 20000.0
    with patch("src.scd30.random", return_value=1):
        result = scd30._in_range("CO2")
        assert result == 40000.0


# ------------------------------------------------------------------------------
