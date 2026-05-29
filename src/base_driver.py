""" Holds Reading and BaseDriver classes, used to standardize drivers 
and their associated readings"""
from abc import ABC, abstractmethod
from typing import Any


class Reading:
    """Cleanly define a sensor reading and add a repr"""
    def __init__(self, name, value, unit) -> None:
        self.name = name
        self.value = value
        self.unit = unit

    def __repr__(self) -> str:
        return f"{self.name}: {self.value} {self.unit}"


class BaseDriver(ABC):
    """BaseDriver class to standardize sensor drivers"""
    def __init__(self, sensor_id: str, config_dict: dict, i2c_bus: Any) -> None:
        self.sensor_id = sensor_id
        self.config_dict = config_dict
        self.description: str = config_dict.get("description", sensor_id)
        self.readings_meta_data: list[dict] = config_dict.get("readings", [])
        self.i2c_bus = i2c_bus
        self.initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Use this base method to initialize sensors"""

    @abstractmethod
    def read(self) -> list[Reading]:
        """Use this base method to initialize sensors"""
