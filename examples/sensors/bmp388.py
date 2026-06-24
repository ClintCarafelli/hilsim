"""Anything that relates to the bmp388 sensor"""

from typing import Any
from random import random

from hilsim.core.sensors import DriverBase, SensorBase
#from hilsim.core.world_state import WorldState


# If sim=False: will import adafruit_bmp3xx


class FakeBMP388(SensorBase):
    """Fake instance of a BMP388, contains the same methods"""

    @property
    def pressure(self) -> float | None:
        """Read the pressure value"""
        self.add_failure_possibility()
        return self.get_return_value("system_pressure")

    @property
    def temperature(self) -> float | None:
        """Read the temperature property"""
        self.add_failure_possibility()
        return self.get_return_value("system_temp")
    

class BMP388Driver(DriverBase):
    """The Driver for the BMP388 Sensor, standardizes sensor to have two
    methods:
         - initialize()
         - read()
    """

    def initialize_sim(self) -> None:
        self.device = self.fake_sensor
        
    def initialize_real(self) -> None:
        import adafruit_bmp3xx  # type: ignore[import-not-found]
        self.device = adafruit_bmp3xx.BMP3XX_I2C(self.i2c_bus)

    def form_vals_dict(self) -> dict:
        return {"system_pressure": self.device.pressure, 
                "system_temp": self.device.temperature}