"""Anything that relates to the bmp388 sensor"""

from typing import Any
from random import random

from src.base_driver import BaseDriver, Reading
from src.SensorExceptions import SensorInitError, SensorReadError

# If sim=False: will import adafruit_bmp3xx


class FakeBMP388:
    """Fake instance of a BMP388, contains the same methods"""

    def __init__(self, config) -> None:
        self.failure_rate = config["failure_rate"]
        self.readings_meta_data = config["readings"]
        self.counter = 0
        self.rand_num = 0.5

    @property
    def pressure(self) -> float | None:
        """Read the pressure value"""
        # query index for correct bounds for reading
        i: int = next(
            i
            for i, meta in enumerate(self.readings_meta_data)
            if meta["name"] == "pressure"
        )
        if self._get_same_random() < self.failure_rate:
            raise RuntimeError("simulated failed reading")

        val = self.readings_meta_data[i]["min"] + random() * (
            self.readings_meta_data[i]["max"] - self.readings_meta_data[i]["min"]
        )
        return val

    @property
    def temperature(self) -> float | None:
        """Read the temperature property"""
        # query index for correct bounds for reading
        i: int = next(
            i
            for i, meta in enumerate(self.readings_meta_data)
            if meta["name"] == "air_temp"
        )
        if self._get_same_random() < self.failure_rate:
            raise RuntimeError("simulated failed reading")

        val = self.readings_meta_data[i]["min"] + random() * (
            self.readings_meta_data[i]["max"] - self.readings_meta_data[i]["min"]
        )
        return val

    # All parameters fail on the same reading (observed real behavior), so same random number
    # should make all properties fail.
    def _get_same_random(self) -> float:
        """save a random number every 2 calls to dictate identical failure behavior across
        both properties"""
        self.counter += 1
        if self.counter % 2 == 0:
            self.rand_num = random()
            return self.rand_num
        return self.rand_num


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
