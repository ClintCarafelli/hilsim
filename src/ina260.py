"""Anything related to the ina260 sensor"""

from typing import Any
from random import random

from src.base_driver import BaseDriver, Reading, SensorBase
from src.sensor_exceptions import SensorInitError, SensorReadError
from src.world_state import WorldState

class FakeINA260(SensorBase):
    """Fake INA260 that does not require physical hardware"""

    def __init__(self, config: dict, world_state: WorldState) -> None:
        super().__init__(config, world_state)
        self.voltage_val = 0.0
        self.current_val = 0.0

    @property
    def voltage(self) -> float | None:
        """Generate voltage value"""
        self.add_failure_possibility()
        self.voltage_val = self.get_return_value("system_voltage")
        return self.voltage_val 

    @property
    def current(self) -> float:
        """Generate current value"""
        self.add_failure_possibility()
        self.current_val = self.get_return_value("system_current")
        return self.current_val

    @property
    def power(self) -> float | None:
        "Generate power value"
        self.add_failure_possibility()
        return self.current_val * self.voltage_val

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
