from src.BaseSensor import Reading, BaseSensor
from src.SensorExceptions import SensorInitError, SensorReadError
from random import random
from src.FakeSTEMMA import FakeSTEMMA
# If sim=False, the following will run: from adafruit_seesaw.seesaw import Seesaw

class STEMMADriver(BaseSensor):

    def __init__(self, sensor_id: str, config_dict: dict, i2c_bus: any, fake_sensor: FakeSTEMMA) -> None: 
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim                     = config_dict["sim"]
        self.i2c_address             = config_dict["i2c_address"]
        self.i2c_bus                 = i2c_bus
        self.fake_sensor             = fake_sensor
        self.sim_fail_initialization = config_dict["sim_fail_initialization"]
        self.device                  = None 

    def initialize(self):
        """ initialize the STEMMA soil moisture sensor driver"""
        try:
            if self.sim:
                if self.sim_fail_initialization:
                    raise Exception("simulated failed initialization")
                self.device = self.fake_sensor
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

