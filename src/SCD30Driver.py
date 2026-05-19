from src.BaseSensor import Reading, BaseSensor
from src.SensorExceptions import SensorInitError, SensorReadError
from datetime import datetime, timedelta
from  random import random

class SCD30Driver(BaseSensor):

    def __init__(self, sensor_id: str, config_dict: dict, i2c_bus: any) -> None:
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim = config_dict["sim"]
        self.failure_rate = config_dict["failure_rate"]

    def initialize(self) -> None:
        """ Initialize the SCD30 sensor"""
        if self.sim: 
            # set_measurement_interval is hard coded because that is the absolute maximum rate the sensor can 
            # read. Slower reading rates are controlled in the main.py /config.txt file
            self.device = FakeSCD30(self.failure_rate)
            self.device.set_measurement_interval(2) 
            self.device.start_periodic_measurement()
            self.initialized = True
        else: 
            try: 
                from scd30_i2c import SCD30
                self.device = SCD30()
                self.device.set_measurement_interval(2) 
                self.device.start_periodic_measurement()
                self.initialized = True
            except Exception as e: 
                raise SensorInitError(self.sensor_id, str(e)) from e

    def read(self) -> list[Reading]:
        """ Read the SCD30 sensor """
        if not self.initialized:
            raise SensorReadError(self.sensor_id, "Sensor not initialized.")
        try: 
            vals = self.device.read_measurment()

        except Exception as e:
            vals = [None, None, None]
            raise SensorReadError(self.sensor_id, str(e)) from e

        return [Reading(m["name"], val, m["units"]) for val, m in zip(vals, self.readings_meta_data)]
        

        
class FakeSCD30:
    """ This is a class that has fake methods and produces fake data for the SCD30 sensor"""
    def __init__(self, failure_rate):
        self.failure_rate = failure_rate

    def set_measurement_interval(self, a: float) -> None: 
        self.measurement_interval = a

    def start_periodic_measurement(self) -> None: 
        self.reading = True 
        self.last_reading_time = datetime.now()

    def get_data_ready(self) -> bool:
        if datetime.now() - self.last_reading_time > timedelta(seconds=self.measurement_interva):
            return True
        else:
            return False

    def read_measurment(self):
        # Bounds are hardcoded since they do not change. Hardware contraint. 
        # Note that if the sensor fails, all three readings fail. 
        if random() < self.failure_rate: 
            return [None, None, None]

        else: 
            CO2 = random() * 40000
            rel_humid = random() * 95
            temp  = random() * 50
            return [CO2, rel_humid, temp]


        

