"""Fake ME2 sensor implementation for testing."""

from random import random


class FakeME2:
    """FAKE ME2 sensor. Contains same method as actual sensor code"""

    def __init__(self, config: dict) -> None:
        self.failure_rate = config["failure_rate"]
        self.readings_meta_data = config["readings"]

    # Collection number isn't actually needed here since it is just used to average
    # samples from the real sensor. Nonetheless it must be an input to keep with the
    # method defined in DFRobot_Oxygen_IIC
    def get_oxygen_data(self, collection_number: int) -> float | None:
        """Generate an oxygen value"""
        if random() < self.failure_rate:
            raise ValueError("simulated failed reading")
        measurements = []
        for _ in range(collection_number):
            min_range = self.readings_meta_data[0]["min"]
            max_range = self.readings_meta_data[0]["max"]
            measurements.append(min_range + random() * (max_range - min_range))
        return sum(measurements) / collection_number

    def check_collection_number(self, collection_number: int):
        """Raise an error over a low collection number which leads to volatile date"""
        if collection_number < 5:
            raise ValueError(
                "ME2 collection number is low; noisy data. "
                "Pick a value greater than 5"
            )
