"""Holds Reading and BaseDriver classes, used to standardize drivers
and their associated readings"""

from abc import ABC, abstractmethod
from typing import Any
from random import random
from src.world_state import WorldState
from src.sensor_exceptions import UnknownVariableName


# ---------------------------------------------------------------------------------------
class Reading:
    """Cleanly define a sensor reading and add a repr"""

    def __init__(self, name, value, unit) -> None:
        self.name = name
        self.value = value
        self.unit = unit

    def __repr__(self) -> str:
        return f"{self.name}: {self.value} {self.unit}"


# ---------------------------------------------------------------------------------------
class BaseDriver(ABC):
    """BaseDriver class to standardize sensor drivers"""

    def __init__(self, sensor_id: str, config_dict: dict, i2c_bus: Any) -> None:
        self.sensor_id = sensor_id
        self.config_dict = config_dict
        self.description: str = config_dict.get("description", sensor_id)
        self.readings_meta_data: list[dict] = config_dict.get("readings", [])
        self.i2c_bus = i2c_bus
        self.initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Use this base method to initialize sensors"""

    @abstractmethod
    def read(self) -> list[Reading]:
        """Use this base method to initialize sensors"""


# ---------------------------------------------------------------------------------------
class SensorBase:
    """Base class for a fake sensor"""

    def __init__(self, config: dict, world_state: WorldState) -> None:
        self.num_measurements = int(config["num_measurements"])
        self.readings_meta_data = config["readings"]
        self.failure_rate = config["failure_rate"]
        self.time = world_state.state["time"]
        self.counter = 0
        self.rand_num = 0
        self.world_state = world_state
        self.rmd_name_map: dict[str, Any] = {}
        self._map_readings_to_noise()

    def _map_readings_to_noise(self) -> None:
        """map readings list of dictonaries to names"""
        for reading in self.readings_meta_data:
            self.rmd_name_map[reading["name"]] = reading

    def add_failure_possibility(self) -> None:
        """Add a simulated failure"""
        if self._get_same_random() < self.failure_rate:
            raise RuntimeError("simulated failed reading")
        return

    def _get_same_random(self) -> float:
        """return the same random n times, here n=3"""
        # reset random number every 3 counts since this function gets called
        # three times for a full sensor read
        if self.counter % self.num_measurements == 0:
            self.counter += 1
            self.rand_num = random()
            return self.rand_num
        self.counter += 1
        return self.rand_num

    def _add_noise_and_drift(self, variable_name: str) -> float:
        """Generate noise to reflect real hardware based on noise/drift parameters"""
        try:
            noise_param = self.rmd_name_map[variable_name]["noise"]
            drift_param = self.rmd_name_map[variable_name]["drift"]
        except Exception as e:
            print(self.rmd_name_map[variable_name])
            print(e)
        noise_val = 2 * (noise_param * (random() - 0.5)) + drift_param * self.time
        return noise_val

    def get_return_value(
        self, variable_name: str, add_noise_and_drift: bool = True
    ) -> float:
        """Generate the return value, factoring in noise and dift and sensor
        min and max"""
        if variable_name not in self.world_state.state.keys():
            print(
                f"{type(self).__name__}, variable_name {variable_name} is not in the world state."
            )
            raise UnknownVariableName(
                type(self).__name__,
                f"variable_name {variable_name} is not in the world state.",
            )
        dynamics_value = self.world_state.get(variable_name)

        if add_noise_and_drift:
            dynamics_value += self._add_noise_and_drift(variable_name)

        sensor_min = self.rmd_name_map[variable_name]["min"]
        sensor_max = self.rmd_name_map[variable_name]["max"]
        clamped = max(sensor_min, min(dynamics_value, sensor_max))
        return clamped


# ---------------------------------------------------------------------------------------
