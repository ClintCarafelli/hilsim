from random import random
from datetime import datetime, timedelta

class FakeSCD30:
    """ This is a class that has fake methods and produces fake data for the SCD30 sensor"""
    def __init__(self, config):
        self.failure_rate       = config["failure_rate"]
        self.readings_meta_data = config["readings"]

    def set_measurement_interval(self, a: float) -> None: 
        self.measurement_interval = a

    def start_periodic_measurement(self) -> None: 
        self.reading = True 
        self.last_reading_time = datetime.now()

    def get_data_ready(self) -> bool:
        if datetime.now() - self.last_reading_time > timedelta(seconds=self.measurement_interval):
            return True
        else:
            return False

    def read_measurement(self) -> list[float]:
        # Bounds are hardcoded since they do not change. Hardware contraint. 
        # Note that if the sensor fails, all three readings fail. 
        if random() < self.failure_rate: 
            raise Exception("simulated failed reading")
        else: 
            CO2_val   = self._in_range("CO2")
            rel_humid = self._in_range("relative_humidity")
            temp      = self._in_range("temp")
            return [CO2_val, rel_humid, temp]
        
    def _in_range(self, name: str) -> float:
         """find random value between min and max of the result"""
         i: int = next(i for i, meta in enumerate(self.readings_meta_data) if meta["name"] == name)
         val: float = self.readings_meta_data[i]["min"] + random() * (self.readings_meta_data[i]["max"] -
                                                                self.readings_meta_data[i]["min"])
         return val


        

