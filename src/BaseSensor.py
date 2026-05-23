from abc import ABC, abstractmethod

class Reading: 
    # DESCRIPTION: solves the issue of trying to print a class.
    # instead of printing out a memory address, this will
    # return the measurment name, value, and unit 
    def __init__(self, name, value, unit) -> None:
        self.name  = name
        self.value = value
        self.unit  = unit

    def __repr__(self) -> str:
        return f"{self.name}: {self.value} {self.unit}"

class BaseSensor(ABC):

    def __init__(self, sensor_id: str, config_dict: dict, i2c_bus: any) -> None: 
        self.sensor_id                      = sensor_id
        self.config_dict                    = config_dict
        self.description: str               = config_dict.get("description", sensor_id)
        self.readings_meta_data: list[dict] = config_dict.get("readings", [])
        self.i2c_bus                        = i2c_bus
        self.initialized                    = False

    @abstractmethod
    def initialize(self) -> None :
        """ Use this base method to initialize sensors"""


    @abstractmethod
    def read(self) -> list[Reading]:
        """ Use this base method to initialize sensors"""

"""
from src.SCD30Driver import SCD30Driver
from src.BMP388Driver import BMP388Driver
from src.STEMMADriver import STEMMADriver
from src.ME2Driver import ME2Driver
from src.INA260Driver import INA260Driver

# Map the class that drives the sensor to the driver field in the config.toml file
driver_registry: dict = {
    "SCD30_driver":   SCD30Driver,
    "BMP388_driver":  BMP388Driver,
    "STEMMA1_driver": STEMMADriver,
    "STEMMA2_driver": STEMMADriver,
    "STEMMA3_driver": STEMMADriver,
    "ME2_driver":     ME2Driver,
    "INA260_driver":  INA260Driver,
}
"""
