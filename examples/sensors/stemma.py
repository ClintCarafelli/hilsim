"""Anything related to the STEMMA sensor"""

from typing import Any
from random import random

from hilsim.core.world_state import WorldState
from hilsim.core.sensors import DriverBase, SensorBase

# If sim=False, the following will run: from adafruit_seesaw.seesaw import Seesaw


class FakeSTEMMA(SensorBase):
    """Provides a fake device / methods for the Stemma soil moisture sensor"""

    def __init__(self, config: dict, world_state: WorldState) -> None: 
        super().__init__(config, world_state)
        self.chip_temp_name = self.get_correct_variable_name("chip_temp")
        self.soil_moisture_name = self.get_correct_variable_name("soil_moisture")
        
    def moisture_read(self) -> float | None:
        """Read the soil moisture value"""
        self.add_failure_possibility()
        return self.get_return_value(self.soil_moisture_name)

    def get_temp(self) -> float | None:
        """Read the onboard chip temperature (a poor proxy for air temp)"""
        self.add_failure_possibility()
        return self.get_return_value(self.chip_temp_name)

class STEMMADriver(DriverBase):
    """Drive the STEMMA sensor, standardizing methods to initialize() and read()"""

    def __init__(
        self, sensor_id: str, config_dict: dict, i2c_bus: Any, fake_sensor: FakeSTEMMA
    ) -> None:
        super().__init__(sensor_id, config_dict, i2c_bus, fake_sensor)
        self.i2c_address = config_dict["i2c_address"]
        self.chip_temp_name = self.get_correct_variable_name("chip_temp")
        self.soil_moisture_name = self.get_correct_variable_name("soil_moisture")

    def initialize_sim(self) -> None:
        self.device = self.fake_sensor
        
    def initialize_real(self) -> None:
         from adafruit_seesaw.seesaw import Seesaw  # type: ignore[import-not-found]
         self.device = Seesaw(self.i2c_bus, self.i2c_address)

    def form_vals_dict(self) -> dict: 
        return {self.soil_moisture_name: self.device.moisture_read(), 
                self.chip_temp_name: self.device.get_temp()}