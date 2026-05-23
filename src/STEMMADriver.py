from src.BaseSensor import Reading, BaseSensor
from src.SensorExceptions import SensorInitError, SensorReadError
from random import random
# If sim=False, the following will run: from adafruit_seesaw.seesaw import Seesaw

class STEMMADriver(BaseSensor):

    def __init__(self, sensor_id: str, config_dict: dict, i2c_bus: any) -> None: 
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim = config_dict["sim"]
        self.failure_rate = config_dict["failure_rate"]
        self.i2c_address = config_dict["i2c_address"]
        self.i2c_bus = i2c_bus

    
    def initialize(self):
        """ initialize the STEMMA soil moisture sensor driver"""
        try:
            if self.sim:
                self.device = FakeSTEMMA(self.failure_rate, self.readings_meta_data)
                self.initialized = True
            else:  
                from adafruit_seesaw.seesaw import Seesaw
                self.device = Seesaw(self.i2c_bus, self.i2c_address)
                self.initialized = True
        except Exception as e: 
            raise SensorInitError(self.sensor_id, str(e)) from e
            
    def read(self):
        """ Reads the Stemma soil moisture sensor"""
        if not self.initialized:
            raise SensorReadError(self.sensor_id, "Sensor not initialized")
        
        try: 
            moisture = self.device.moisture_read()
            temp = self.device.get_temp()
            vals = [moisture, temp]

        except Exception as e: 
            raise SensorReadError(self.sensor_id, str(e)) from e
        
        return [Reading(m["name"], val, m["units"]) for val, m in zip(vals, self.readings_meta_data)]
      
class FakeSTEMMA:
    """ Provides a fake device / methods for the Steamma soil moisture sensor"""
    def __init__(self, failure_rate: float, readings_meta_data: dict) -> None:
        self.failure_rate = failure_rate
        self.readings_meta_data = readings_meta_data
        self.counter = 0
        self.rand_num = 0.5

    def moisture_read(self) -> float | None:
        if self._get_same_random() < self.failure_rate:
            raise Exception("simulated failed reading")
        else: 
            return self._in_range("moisture")
        
    def get_temp(self) -> float | None:
        if self._get_same_random() < self.failure_rate:
            raise Exception("simulated failed reading")
        else: 
            return self._in_range("temp")

    def _in_range(self, name: str) -> float:
         """find random value between min and max of the result"""
         i: int = next(i for i, meta in enumerate(self.readings_meta_data) if meta["name"] == name)
         val: float = self.readings_meta_data[i]["min"] + random() * (self.readings_meta_data[i]["max"] -
                                                                self.readings_meta_data[i]["min"])
         return val
    
    # See comments in BMP388 Driver for information about this function and why the random number is
    # constructed in this way
    def _get_same_random(self) -> float:
        # reset random number every 2 counts since this function gets called twice for a full sensor read
        self.counter += 1
        if self.counter % 2 == 0:
            self.rand_num = random()
            return self.rand_num
        else: 
            return self.rand_num
