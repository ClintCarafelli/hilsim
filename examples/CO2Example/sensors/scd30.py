"""the SCD30 Sensor"""

from datetime import datetime, timedelta
from random import random

from hilsim.core.sensors import DriverBase, SensorBase

# if sim=False, will import SCD30 from scd30_i2c


class FakeSCD30(SensorBase):
    """This is a class that has fake methods and produces fake data for the SCD30 sensor"""

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
        # Note that if the sensor fails, all three readings fail to keep with
        # observed behavior
      
        self.add_failure_possibility()
        co2_val = self.get_return_value("CO2")
        rel_humid = self.get_return_value("relative_humidity")
        temp = self.get_return_value("temperature")

        return [co2_val, rel_humid, temp]


class SCD30Driver(DriverBase):
    """SCSD30 Driver that standardizes methods to initialize and read"""

    def initialize_sim(self) -> None:
        """Initialize sim mode for an SCD30 driver"""
        self.device = self.fake_sensor
        self.device.set_measurement_interval(0.1)
        self.device.start_periodic_measurement()
        
    def initialize_real(self) -> None:
        """Initialize real mode for an SCD30 Driver"""
        from scd30_i2c import SCD30  # type: ignore[import-not-found]
        self.device = SCD30()
        self.device.set_measurement_interval(0.1)
        self.device.start_periodic_measurement()

    def form_vals_dict(self) -> dict: 
        """Create dictonary of sensor readings"""
        vals = self.device.read_measurement()
        return {"CO2": vals[0], 
                "relative_humidity": vals[1], 
                "temperature": vals[2]}
