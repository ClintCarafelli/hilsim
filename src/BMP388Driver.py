from src.BaseSensor import Reading, BaseSensor
from src.SensorExceptions import SensorInitError, SensorReadError
from  random import random
# If sim=False: will import adafruit_bmp3xx

class BMP388Driver(BaseSensor):

    def __init__(self, sensor_id: str, config_dict: dict, i2c_bus: any) -> None:
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim = config_dict["sim"]
        self.failure_rate = config_dict["failure_rate"]

    def initialize(self) -> None:
        if self.sim:
            self.device = FakeBMP388(self.failure_rate, self.readings_meta_data)
            self.initialized = True
        else: 
            try: 
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
            vals = [None, None]
            raise SensorReadError(self.sensor_id, str(e)) from e
        
        return [Reading(m["name"], val, m["units"]) for val, m in zip(vals, self.readings_meta_data)]

            
class FakeBMP388: 
    def __init__(self, failure_rate, readings_meta_data) -> None:
        self.failure_rate = failure_rate
        self.rand_num = random()
        self.readings_meta_data = readings_meta_data

    @property
    def pressure(self) -> float | None:
        i: int = next(i for i, meta in enumerate(self.readings_meta_data) if meta["name"] == "pressure")
        if self.rand_num < self.failure_rate:
            return None 
        else:
            return self.readings_meta_data[i]["min"] + random() * (self.readings_meta_data[i]["max"] - self.readings_meta_data[i]["min"])

    # reset self.rand_num in temp setting to actually get the random number to change. Done by convetion in temp
    # because it is called second in the read function, keeping with the idea that both pressure and 
    # temperature failure should be set by the same random number generator because they always fail 
    # together
    @property
    def temperature(self)-> float | None:
        i: int = next(i for i, meta in enumerate(self.readings_meta_data) if meta["name"] == "air_temp")
        if self.rand_num < self.failure_rate:
            self.rand_num= random()
            return None 
        else:
             self.rand_num= random()
             return self.readings_meta_data[i]["min"] + random() * (self.readings_meta_data[i]["max"] - self.readings_meta_data[i]["min"])

