"""Drive the ME2 sensor, including initialize and read"""

from typing import Any
from random import random

from src.base_driver import BaseDriver, Reading
from src.sensor_exceptions import SensorInitError, SensorReadError

# If sim=False, the following will run: DFRobot_Oxygen import DFRobot_Oxygen_IIC



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


class ME2Driver(BaseDriver):
    """Drive the ME2 sensor, including initialize and read"""

    def __init__(
        self, sensor_id: str, config_dict: dict, i2c_bus: Any, fake_sensor: FakeME2
    ) -> None:
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim = config_dict["sim"]
        self.iic_mode = config_dict["IIC_mode"]
        self.i2c_address = config_dict["i2c_address"]
        self.collection_number = config_dict["collection_number"]
        self.sim_fail_initialization = config_dict["sim_fail_initialization"]
        self.fake_sensor = fake_sensor
        self.sensor_id = sensor_id

    def initialize(self) -> None:
        """Initialize the ME2 (DFRobot) oxygen sensor"""
        try:
            if self.sim:
                if self.sim_fail_initialization:
                    raise Exception("simulate failed initialization")
                self.device = self.fake_sensor
                self.initialized = True
            else:
                from DFRobot_Oxygen import \
                    DFRobot_Oxygen_IIC  # type: ignore[import-not-found]

                self.device = DFRobot_Oxygen_IIC(self.iic_mode, self.i2c_address)
                self.initialized = True
        except Exception as e:
            raise SensorInitError(self.sensor_id, str(e)) from e

    def read(self) -> list[Reading]:
        """Read the ME2 oxygen sensor"""
        if not self.initialized:
            raise SensorReadError(self.sensor_id, "Sensor not initialized")
        try:
            vals = self.device.get_oxygen_data(self.collection_number)

        except Exception as e:
            raise SensorReadError(self.sensor_id, str(e)) from e

        return [
            Reading(
                self.readings_meta_data[0]["name"],
                vals,
                self.readings_meta_data[0]["units"],
            )
        ]
