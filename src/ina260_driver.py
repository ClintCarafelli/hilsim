"""Driver for INA260 Sensor"""

from typing import Any

from src.base_driver import BaseDriver, Reading
from src.fake_ina260 import FakeINA260
from src.SensorExceptions import SensorInitError, SensorReadError


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
