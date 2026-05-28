from src.BaseSensor import Reading, BaseSensor
from src.SensorExceptions import SensorInitError, SensorReadError
from src.FakeBMP388 import FakeBMP388
from  random import random
# If sim=False: will import adafruit_bmp3xx

class BMP388Driver(BaseSensor):
    def __init__(self, sensor_id: str, config_dict: dict, i2c_bus: any, fake_sensor: FakeBMP388) -> None:
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim                     = config_dict["sim"]
        self.sim_fail_initialization = config_dict["sim_fail_initialization"]
        self.device                  = None
        self.fake_sensor             = fake_sensor

    def initialize(self) -> None:
        try: 
            if self.sim:
                if self.sim_fail_initialization: 
                    raise Exception("simulated initialization failure.")
                self.device = self.fake_sensor
                self.initialized = True
            else:  
                import adafruit_bmp3xx
                self.device = adafruit_bmp3xx.BMP3XX_I2C(self.i2c_bus)
                self.initialized = True
        except Exception as e: 
            raise  SensorInitError(self.sensor_id, str(e)) from e
            
    def read(self) -> list[Reading]:
        if not self.initialized:
            raise SensorReadError(self.sensor_id, "Sensor not initialized.")
        try:
            pressure = self.device.pressure
            temp = self.device.temperature
            vals = [pressure, temp]

        except Exception as e: 
            raise SensorReadError(self.sensor_id, str(e)) from e
        
        return [Reading(m["name"], val, m["units"]) for val, m in zip(vals, self.readings_meta_data)]

