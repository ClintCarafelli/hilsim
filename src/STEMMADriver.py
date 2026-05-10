from BaseSensor import Reading, BaseSensor
from SensorExceptions import SensorInitError, SensorReadError
from random import random
# If sim=False, the following will run: from adafruit_seesaw.seesaw import Seesaw

class STEMMADriver(BaseSensor):

    def __init__(self, sensor_id: str, config_dict: dict, i2c_bus: any) -> None: 
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim = config_dict["sim"]
        self.failure_rate = config_dict["failure_rate"]
        self.i2c_address = config_dict["i2c_address"]

    
    def initialize(self):
        """ initialize the STEMMA soil moisture sensor driver"""
        if self.sim:
            self.device = FakeSTEMMA(self.failure_rate, self.readings_meta_data)
            self.initialized = True
        else: 
            try: 
                from adafruit_seesaw.seesaw import Seesaw
                self.device = Seesaw(i2c_object, self.i2c_address)
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
            vals = [None,None]
            raise SensorReadError(self.sensor_id, str(e)) from e
        
        return [Reading(m["name"], val, m["units"]) for val, m in zip(vals, self.readings_meta_data)]
      
class FakeSTEMMA:
    """ Provides a fake device / methods for the Steamma soil moisture sensor"""
    def __init__(self, failure_rate: float, readings_meta_data: dict) -> None:
        self.failure_rate = failure_rate
        self.rand_num = random()
        self.readings_meta_data = readings_meta_data

    def moisture_read(self) -> float | None:
        if self.rand_num < self.failure_rate:
            return None
        else: 
            i: int = next(i for i, meta in enumerate(self.readings_meta_data) if meta["name"] == "moisture")
            return  self.readings_meta_data[i]["min"] + random() * ( self.readings_meta_data[i]["max"] -  self.readings_meta_data[i]["min"])
        
    # reset self.rand_num in temp setting to actually get the random number to change. Done by convetion in temp
    # because it is called second in the read function, keeping with the idea that both pressure and 
    # temperature failure should be set by the same random number generator because they always fail 
    # together
    def get_temp(self) -> float | None:
        if self.rand_num < self.failure_rate:
            self.rand_num = random()
            return None
        else: 
            self.rand_num = random()
            i: int = next(i for i, meta in enumerate(self.readings_meta_data) if meta["name"] == "temp")
            return  self.readings_meta_data[i]["min"] + random() * ( self.readings_meta_data[i]["max"] -  self.readings_meta_data[i]["min"])

