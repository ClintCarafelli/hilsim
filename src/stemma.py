"""Anything related to the STEMMA sensor"""

from typing import Any
from random import random

from src.world_state import WorldState
from src.base_driver import BaseDriver, Reading, SensorBase
from src.sensor_exceptions import SensorInitError, SensorReadError

# If sim=False, the following will run: from adafruit_seesaw.seesaw import Seesaw


class FakeSTEMMA(SensorBase):
    """Provides a fake device / methods for the Stemma soil moisture sensor"""

    def __init__(self, config: dict, world_state: WorldState) -> None: 
        super().__init__(config, world_state)
        self.chip_temp_name = config
        
    def moisture_read(self) -> float | None:
        """Read the soil moisture value"""
        self.add_failure_possibility()
        return self.get_return_value("soil_moisture")

    def get_temp(self) -> float | None:
        """Read the onboard chip temperature (a poor proxy for air temp)"""
        self.add_failure_possibility()
        return self.get_return_value("stemma_chip_temp")

class STEMMADriver(BaseDriver):
    """Drive the STEMMA sensor, standardizing methods to initialize() and read()"""

    def __init__(
        self, sensor_id: str, config_dict: dict, i2c_bus: Any, fake_sensor: FakeSTEMMA
    ) -> None:
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim = config_dict["sim"]
        self.i2c_address = config_dict["i2c_address"]
        self.i2c_bus = i2c_bus
        self.fake_sensor = fake_sensor
        self.sim_fail_initialization = config_dict["sim_fail_initialization"]

    def initialize(self) -> None:
        """initialize the STEMMA soil moisture sensor driver"""
        try:
            if self.sim:
                if self.sim_fail_initialization:
                    raise Exception("simulated failed initialization")
                self.device = self.fake_sensor
                self.initialized = True
            else:
                from adafruit_seesaw.seesaw import \
                    Seesaw  # type: ignore[import-not-found]

                self.device = Seesaw(self.i2c_bus, self.i2c_address)
                self.initialized = True
        except Exception as e:
            raise SensorInitError(self.sensor_id, str(e)) from e

    def read(self) -> list[Reading]:
        """Reads the Stemma soil moisture sensor"""
        if not self.initialized:
            raise SensorReadError(self.sensor_id, "Sensor not initialized")

        try:
            moisture = self.device.moisture_read()
            temp = self.device.get_temp()
            vals = [moisture, temp]

        except Exception as e:
            raise SensorReadError(self.sensor_id, str(e)) from e

        return [
            Reading(m["name"], val, m["units"])
            for val, m in zip(vals, self.readings_meta_data)
        ]
