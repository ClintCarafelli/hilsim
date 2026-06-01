"""Driver for the SCD30 Sensor"""

from typing import Any

from src.base_driver import BaseDriver, Reading
from src.fake_scd30 import FakeSCD30
from src.SensorExceptions import SensorInitError, SensorReadError

# if sim=False, will import SCD30 from scd30_i2c


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
