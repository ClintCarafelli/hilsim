"""Test the BaseDriver class and the Reading class"""

import pytest
from src.base_driver import Reading, BaseDriver


# ---------------------------------------------------------------------------------------
# Testing Reading class
@pytest.fixture
def example_reading() -> Reading:
    """Create an example reading for testing"""
    return Reading("CO2", 1200, "ppm")


def test_reading_attributes(example_reading: Reading) -> None:
    """Test reading return is correct"""
    assert example_reading.name == "CO2"
    assert example_reading.value == 1200
    assert example_reading.unit == "ppm"


def test_reading_repr(example_reading: Reading) -> None:
    """Ensure repr is correct"""
    assert repr(example_reading) == "CO2: 1200 ppm"


# ---------------------------------------------------------------------------------------
#  BaseDriver tests

READINGS_LIST: list[dict] = [
    {"name": "CO2", "units": "ppm", "min": 0, "max": 40000},
    {"name": "temp", "units": "C", "min": 0, "max": 65},
]
NOMINAL_CONFIG_DICT: dict = {"description": "sensor_description", "readings": READINGS_LIST}
TEST_GET_CONFIG_DICT: dict = {}
SENSOR_ID: str = "SCD30"
I2C_BUS: None = None


class MockDriver(BaseDriver):
    """Create a mock sensor that inherits form BaseDriver"""

    def initialize(self) -> None:
        """Must be included, enforced as abstractmethod"""
        self.initialized = True

    def read(self) -> list:
        """Must be included, enforced as abstractmethod"""
        return []


def test_base_driver_nominal_init() -> None:
    """Test BaseDriver with complete input"""
    base_sensor = MockDriver(SENSOR_ID, NOMINAL_CONFIG_DICT, I2C_BUS)
    assert base_sensor.initialized is False
    assert base_sensor.description == "sensor_description"
    assert base_sensor.readings_meta_data == READINGS_LIST


def test_base_driver_no_description_or_readings_init() -> None:
    """Test BaseDriver call with optional inputs"""
    base_sensor = MockDriver(SENSOR_ID, TEST_GET_CONFIG_DICT, I2C_BUS)
    assert base_sensor.initialized is False
    assert base_sensor.description == SENSOR_ID
    assert base_sensor.readings_meta_data == []


def test_base_driver_is_abstract() -> None:
    """Ensure BaseDriver inherits from ABC (abstract)"""
    with pytest.raises(TypeError):
        BaseDriver(SENSOR_ID, NOMINAL_CONFIG_DICT, I2C_BUS) # type: ignore[abstract]


# ---------------------------------------------------------------------------------------
