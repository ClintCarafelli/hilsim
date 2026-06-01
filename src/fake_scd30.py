"""Fake SCD30 that does not require hardware"""

from datetime import datetime, timedelta
from random import random


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
