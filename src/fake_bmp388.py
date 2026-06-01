"""Fake BMP388 Sensor. Contains the same methods as actual sensor class"""

from random import random


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
