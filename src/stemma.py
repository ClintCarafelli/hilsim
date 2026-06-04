"""Anything related to the STEMMA sensor"""

from typing import Any
from random import random

from src.base_driver import BaseDriver, Reading
from src.SensorExceptions import SensorInitError, SensorReadError

# If sim=False, the following will run: from adafruit_seesaw.seesaw import Seesaw


class FakeSTEMMA:
    """Provides a fake device / methods for the Steamma soil moisture sensor"""

    def __init__(self, config) -> None:
        self.failure_rate = config["failure_rate"]
        self.readings_meta_data = config["readings"]
        self.counter = 0
        self.rand_num = 0.0

    def moisture_read(self) -> float | None:
        """Read the soil moisture value"""
        if self._get_same_random() < self.failure_rate:
            raise Exception("simulated failed reading")
        return self._in_range("moisture")

    def get_temp(self) -> float | None:
        """Read the onboard chip temperature (a poor proxy for air temp)"""
        if self._get_same_random() < self.failure_rate:
            raise Exception("simulated failed reading")
        return self._in_range("temp")

    def _in_range(self, name: str) -> float:
        """find random value between a min and max"""
        i: int = next(
            i for i, meta in enumerate(self.readings_meta_data) if meta["name"] == name
        )
        val: float = self.readings_meta_data[i]["min"] + random() * (
            self.readings_meta_data[i]["max"] - self.readings_meta_data[i]["min"]
        )
        return val

    # Return same random evevery 2 calls so both get_temp and moisture_read
    # fail together (analgous to real hardware behavior)
    def _get_same_random(self) -> float:
        """Get the same random to standardize failure across methods"""
        # reset random number every 2 counts since this function gets called twice for a full sensor read
        self.counter += 1
        if self.counter % 2 == 0:
            self.rand_num = random()
            return self.rand_num
        return self.rand_num


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
