"""Drive a BMP388 Sensor: read and initialize"""

from typing import Any

from src.base_driver import BaseDriver, Reading
from src.fake_bmp388 import FakeBMP388
from src.SensorExceptions import SensorInitError, SensorReadError

# If sim=False: will import adafruit_bmp3xx


class BMP388Driver(BaseDriver):
    """The Driver for the BMP388 Sensor, standardizes sensor to have two
    methods:
         - initialize()
         - read()
    """

    def __init__(
        self, sensor_id: str, config_dict: dict, i2c_bus: Any, fake_sensor: FakeBMP388
    ) -> None:
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim = config_dict["sim"]
        self.sim_fail_initialization = config_dict["sim_fail_initialization"]
        # self.device = None
        self.fake_sensor = fake_sensor

    def initialize(self) -> None:
        """Initialize the sensor, run once at start up"""
        try:
            if self.sim:
                if self.sim_fail_initialization:
                    raise SensorInitError(
                        self.sensor_id, "simulated initialization failure."
                    )
                self.device = self.fake_sensor
                self.initialized = True
            else:
                import adafruit_bmp3xx  # type: ignore[import-not-found]

                self.device = adafruit_bmp3xx.BMP3XX_I2C(self.i2c_bus)
                self.initialized = True
        except Exception as e:
            raise SensorInitError(self.sensor_id, str(e)) from e

    def read(self) -> list[Reading]:
        """Read the sensor, can be called continuously"""
        if not self.initialized:
            raise SensorReadError(self.sensor_id, "Sensor not initialized.")
        try:
            pressure = self.device.pressure
            temp = self.device.temperature
            vals = [pressure, temp]

        except Exception as e:
            raise SensorReadError(self.sensor_id, str(e)) from e

        return [
            Reading(m["name"], val, m["units"])
            for val, m in zip(vals, self.readings_meta_data)
        ]
