import pytest
from unittest.mock import patch, MagicMock
from src.SCD30Driver import SCD30Driver, FakeSCD30
from src.SensorExceptions import SensorInitError, SensorReadError
from datetime import datetime, timedelta


sensor_id = "SCD30"
i2c_bus   = None 
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
def base_config():
    return {"sensor_id": sensor_id,
            "readings": reading_list,
            "i2c_bus": i2c_bus,
            "sim": False,
            "failure_rate": 0}

@pytest.fixture
def sim_success_config(base_config):
    return {**base_config, "sim":True}

@pytest.fixture
def sim_driver(sim_success_config):
    return SCD30Driver(sensor_id, sim_success_config, i2c_bus)

@pytest.fixture
def real_driver(base_config):
    return SCD30Driver(sensor_id, base_config, i2c_bus)

def test_sim_initialization(sim_driver):
    fake_driver = MagicMock()
    with patch("src.SCD30Driver.FakeSCD30", return_value=fake_driver) as mock_fakeSCD30:
        sim_driver.initialize()
        assert sim_driver.device is fake_driver
        assert sim_driver.initialized is True
        mock_fakeSCD30.assert_called_once_with(sim_driver.failure_rate, sim_driver.readings_meta_data)
        sim_driver.device.set_measurement_interval.assert_called_once_with(2)
        sim_driver.device.start_periodic_measurement.assert_called_once_with()

def test_sim_initialization_failure(sim_driver):
    with patch("src.SCD30Driver.FakeSCD30", side_effect=Exception("fail")):
        with pytest.raises(SensorInitError):
            sim_driver.initialize()
        assert sim_driver.initialized is False

def test_real_initialization(real_driver):
    mock_device = MagicMock()
    fake_SCD30_class = MagicMock(return_value=mock_device)
    with patch.dict("sys.modules", {"scd30_i2c": MagicMock(SCD30=fake_SCD30_class)}):
        real_driver.initialize()
        assert real_driver.device is mock_device
        assert real_driver.initialized is True
        real_driver.device.set_measurement_interval.assert_called_once_with(2)
        real_driver.device.start_periodic_measurement.assert_called_once_with()

#- - - - 
# test initialization failure!!!
def test_real_initialization_failure(real_driver):
    fake_SCD30_class = MagicMock(side_effect=Exception("fail"))
    with patch.dict("sys.modules", {"scd30_i2c": MagicMock(SCD30=fake_SCD30_class)}):
        with pytest.raises(SensorInitError):
            real_driver.initialize()
        assert real_driver.initialized is False

def test_read_not_initialized(real_driver):
    with pytest.raises(SensorReadError):
        real_driver.read()

def test_read_success(real_driver):
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.read_measurement.return_value = [1,2,3]
    result = real_driver.read()
    assert result[0].value == 1
    assert result[1].value == 2
    assert result[2].value == 3
    assert len(result) == 3

def test_read_failure(real_driver):
    real_driver.initialized = True
    real_driver.device = MagicMock()
    real_driver.device.read_measurement.side_effect = Exception("fail")
    with pytest.raises(SensorReadError):
        result = real_driver.read()

@pytest.fixture
def patch_time():
    return datetime(2024, 1, 1, 0, 0, 0)

@pytest.fixture
def SCD30():
    return FakeSCD30(0, reading_list)

def test_FakeSCD30_set_measurement_interval(SCD30):
    SCD30.set_measurement_interval(2)
    assert SCD30.measurement_interval == 2


def test_FakeSCD30_start_periodic_measurement(SCD30, patch_time):
    with patch("src.SCD30Driver.datetime") as mock_dt:
        mock_dt.now.return_value = patch_time
        SCD30.start_periodic_measurement()
        assert SCD30.reading is True 
        assert SCD30.last_reading_time == patch_time

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
    with patch("src.SCD30Driver.datetime") as mock_dt: 
        mock_dt.now.return_value = patch_time + timedelta(seconds=time_diff)
        result = SCD30.get_data_ready()
        if time_diff == 1: 
            assert result is False
        if time_diff == 2: 
            assert result is False
        if time_diff == 3: 
            assert result is True

def test_FakeSCD30_read_measurement_success(SCD30):
    with patch("src.SCD30Driver.random", return_value = 0.5): 
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

def test_in_range(SCD30):
    with patch("src.SCD30Driver.random", return_value = 0.0):
        result = SCD30._in_range("CO2")
        assert result == 0.0
    with patch("src.SCD30Driver.random", return_value = 0.5):
        result = SCD30._in_range("CO2")
        assert result == 20000.0
    with patch("src.SCD30Driver.random", return_value = 1):
        result = SCD30._in_range("CO2")
        assert result == 40000.0

    






    








    

