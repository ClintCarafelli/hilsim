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
        try: 
            if self.sim:
                self.device = FakeBMP388(self.failure_rate, self.readings_meta_data)
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

            
class FakeBMP388: 
    def __init__(self, failure_rate, readings_meta_data,) -> None:
        self.failure_rate = failure_rate
        self.readings_meta_data = readings_meta_data
        self.counter = 0
        self.rand_num = 0.5

    @property
    def pressure(self) -> float | None:
        # query index for correct bounds for reading 
        i: int = next(i for i, meta in enumerate(self.readings_meta_data) if meta["name"] == "pressure")
        if self._get_same_random() < self.failure_rate:
            raise Exception("simulated failed reading")
        else:
            val = self.readings_meta_data[i]["min"] + random() * (self.readings_meta_data[i]["max"] - self.readings_meta_data[i]["min"])
        return val
    
    @property
    def temperature(self)-> float | None:
        # query index for correct bounds for reading
        i: int = next(i for i, meta in enumerate(self.readings_meta_data) if meta["name"] == "air_temp")
        if self._get_same_random() < self.failure_rate:
            raise Exception("simulated failed reading")
        else:
            val = self.readings_meta_data[i]["min"] + random() * (self.readings_meta_data[i]["max"] - self.readings_meta_data[i]["min"])
        return val 
    

    # When these sensors are actually implimented, they never fail on a single parameter read, 
    # rather they all fail together (likey due to impedance / emi on the data lines leading to an 
    # unrecognizable i2c address and therefore a failed reading for all parameters. Hence I
    # have tied the failure of indivdual parameters together by making the random number that
    # dictates failure only reset after both functions are called (they are never called in isolation))
    def _get_same_random(self) -> float:
        # reset random number every2 counts since this function gets called twice for a full sensor read
        self.counter += 1
        if self.counter % 2 == 0:
            self.rand_num = random()
            return self.rand_num
        else: 
            return self.rand_num

