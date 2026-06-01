"""Fake STEMMA that does not require real hardware to run"""

from random import random


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
