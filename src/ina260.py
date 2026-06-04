"""Anything related to the ina260 sensor"""

from typing import Any
from random import random

from src.base_driver import BaseDriver, Reading
from src.sensor_exceptions import SensorInitError, SensorReadError

class FakeINA260:
    """Fake INA260 that does not require physical hardware"""

    def __init__(self, config) -> None:
        self.config = config
        self.voltage_val = 0.0
        self.current_val = 0.0
        self.power_val = 0.0
        self.rand_num = 0.0
        self.counter = 0
        self.status: dict[str, str] = {}
        self.controls_running = False

    @property
    def voltage(self) -> float | None:
        """Generate voltage value"""
        if self._get_same_random() < self.config["failure_rate"]:
            raise Exception("simulated failed reading")

        ps_V = self.config["base_states"]["power_supply"]["voltage"]
        self.voltage_val = ps_V + self._create_noise("base", "power_supply")
        return self.voltage_val

    @property
    def current(self) -> float:
        """Generate current value"""
        if self._get_same_random() < self.config["failure_rate"]:
            raise Exception("simulated failed reading")
        if not self.controls_running:
            self.update_current()
        return self.current_val

    @property
    def power(self) -> float | None:
        "Generate power value"
        if self._get_same_random() < self.config["failure_rate"]:
            raise Exception("simulated failed reading")
        return self.current_val * self.voltage_val

    def update_current(self, status: dict | None = None) -> None:
        """Take in hardware states and update expected current"""
        computer_current = self.config["base_states"]["computer"]["current"]
        current_output = computer_current + self._create_noise("base", "computer")
        if status is not None:
            self.status = status
        for hw_object, state in self.status.items():
            if state == "on":
                object_current = self.config["hardware_states"][hw_object]["on"]
                random_factor = self._create_noise("hardware", hw_object)
            else:
                object_current = 0
                random_factor = 0
            current_output = object_current + random_factor + current_output
        self.current_val = current_output

    def set_status(self, status:dict) -> None:
        """set the status (i.e. known hardware states)"""
        self.status = status

    # Same random should dictate failure of all three measurements because in practice
    # they all fail together
    def _get_same_random(self) -> float:
        """return the same random n times, here n=3"""
        # reset random number every 3 counts since this function gets called
        # three times for a full sensor read
        if self.counter % 3 == 0:
            self.counter += 1
            self.rand_num = random()
            return self.rand_num
        self.counter += 1
        return self.rand_num

    def _create_noise(self, category: str, hw_object: str) -> float:
        """Generate noise to reflect real hardware based on noise parameter"""
        if category == "base":
            noise_param = self.config["base_states"][hw_object]["noise"]
            noise_val = 2 * (noise_param * (random() - 0.5))
            return noise_val
        if category == "hardware":
            noise_param = self.config["hardware_states"][hw_object]["noise"]
            noise_val = 2 * (noise_param * (random() - 0.5))
            return noise_val
        return 0

class INA260Driver(BaseDriver):
    """Driver for INA260 sensor, standardizes sensor to initialize() and read()"""

    def __init__(
        self, sensor_id: str, config_dict: dict, i2c_bus: Any, fake_sensor: FakeINA260
    ) -> None:
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim = config_dict["sim"]
        self.failure_rate = config_dict["failure_rate"]
        self.sim_fail_initialization = config_dict["sim_fail_initialization"]
        self.fake_sensor = fake_sensor

    def initialize(self) -> None:
        """Initialize the INA260 sensor"""
        try:
            if self.sim:
                if self.sim_fail_initialization:
                    raise Exception("simulate failed initialization")
                self.device = self.fake_sensor
                self.initialized = True
            else:
                import adafruit_ina260  # type: ignore[import-not-found]

                self.device = adafruit_ina260.INA260(self.i2c_bus)
                self.initialized = True
        except Exception as e:
            raise SensorInitError(self.sensor_id, str(e)) from e

    def read(self) -> list[Reading]:
        """Read the INA260 SCD30 sensor"""
        if not self.initialized:
            raise SensorReadError(self.sensor_id, "Sensor not initialized")

        try:
            voltage = self.device.voltage
            current = self.device.current
            power = self.device.power
            vals = [voltage, current, power]

        except Exception as e:
            raise SensorReadError(self.sensor_id, str(e)) from e

        return [
            Reading(m["name"], val, m["units"])
            for val, m in zip(vals, self.readings_meta_data)
        ]
