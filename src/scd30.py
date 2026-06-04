"""Anything related to the SCD30 Sensor"""

from typing import Any
from datetime import datetime, timedelta
from random import random

from src.base_driver import BaseDriver, Reading
from src.sensor_exceptions import SensorInitError, SensorReadError

# if sim=False, will import SCD30 from scd30_i2c


class FakeSCD30:
    """This is a class that has fake methods and produces fake data for the SCD30 sensor"""

    def __init__(self, config):
        self.failure_rate = config["failure_rate"]
        self.readings_meta_data = config["readings"]

    def set_measurement_interval(self, a: float) -> None:
        """Set how often the sensor measures"""
        self.measurement_interval = a
        # Could reflect 2 sec max rate here

    def start_periodic_measurement(self) -> None:
        """Begin periodic readings of the sensor"""
        self.reading = True
        self.last_reading_time = datetime.now()

    def get_data_ready(self) -> bool:
        """Determine if data is ready based on measurement_interval"""
        if datetime.now() - self.last_reading_time > timedelta(
            seconds=self.measurement_interval
        ):
            return True
        return False

    def read_measurement(self) -> list[float]:
        """Read a measurement (i.e. return values)"""
        # Bounds are hardcoded since they do not change. Hardware contraint.
        # Note that if the sensor fails, all three readings fail.
        if random() < self.failure_rate:
            raise Exception("simulated failed reading")

        co2_val = self._in_range("CO2")
        rel_humid = self._in_range("relative_humidity")
        temp = self._in_range("temp")
        return [co2_val, rel_humid, temp]

    def _in_range(self, name: str) -> float:
        """find random value between min and max of the result"""
        i: int = next(
            i for i, meta in enumerate(self.readings_meta_data) if meta["name"] == name
        )
        val: float = self.readings_meta_data[i]["min"] + random() * (
            self.readings_meta_data[i]["max"] - self.readings_meta_data[i]["min"]
        )
        return val


class SCD30Driver(BaseDriver):
    """SCSD30 Driver that standardizes methods to initialize and read"""

    def __init__(
        self, sensor_id: str, config_dict: dict, i2c_bus: Any, fake_sensor: FakeSCD30
    ) -> None:
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim = config_dict["sim"]
        self.sim_fail_initialization = config_dict["sim_fail_initialization"]
        # self.device = None
        self.fake_sensor = fake_sensor

    def initialize(self) -> None:
        """Initialize the SCD30 sensor"""
        try:
            if self.sim:
                if self.sim_fail_initialization:
                    raise Exception("simulated initialization failure")
                # set_measurement_interval is hard coded because that is the absolute maximum
                # rate the sensor can read. Slower reading rates are
                # controlled in the main.py /config.txt file
                self.device = self.fake_sensor
                self.device.set_measurement_interval(2)
                self.device.start_periodic_measurement()
                self.initialized = True
            else:
                from scd30_i2c import SCD30  # type: ignore[import-not-found]

                self.device = SCD30()
                self.device.set_measurement_interval(2)
                self.device.start_periodic_measurement()
                self.initialized = True
        except Exception as e:
            raise SensorInitError(self.sensor_id, str(e)) from e

    def read(self) -> list[Reading]:
        """Read the SCD30 sensor"""
        if not self.initialized:
            raise SensorReadError(self.sensor_id, "Sensor not initialized.")
        try:
            # these vals MUST be in the exact order as readings_meta_data which is a
            # list of dictonaries
            vals = self.device.read_measurement()
        except Exception as e:
            raise SensorReadError(self.sensor_id, str(e)) from e

        return [
            Reading(m["name"], val, m["units"])
            for val, m in zip(vals, self.readings_meta_data)
        ]
