from src.BaseSensor import BaseSensor, Reading
from src.SensorExceptions import SensorInitError, SensorReadError
from random import random

class INA260Driver(BaseSensor): 
    def __init__(self, sensor_id: str, config_dict: dict, i2c_bus: any) -> None: 
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim = config_dict["sim"]
        self.failure_rate = config_dict["failure_rate"]

    def initialize(self) -> None: 
        """ Initialize the INA260 sensor """
        if self.sim: 
            self.device = FakeINA260(self.failure_rate, self.readings_meta_data)
            self.initialized = True

        else: 
            try: 
                import adafruit_ina260
                ina260 = adafruit_ina260.INA260(self.i2c_bus)
                self.initialized = True
            except Exception as e: 
                raise SensorInitError(self.sensor_id, str(e)) from e
            

    def read(self) -> list[Reading]:
        """ Read the INA260 SCD30 sensor"""
        if not self.initialized:
            raise SensorReadError(self.sensor_id, "Sensor not initialized")
        
        try: 
            voltage = self.device.voltage
            current = self.device.current
            power   = self.device.power
            vals    = [voltage, current, power]

        except Exception as e: 
            vals = [None, None, None]
            raise SensorReadError(self.sensor_id, str(e)) from e
        
        return [Reading(m["name"], val, m["units"]) for val, m in zip(vals, self.readings_meta_data)]
    

class FakeINA260:
    def __init__(self, failure_rate: float, readings_meta_data: dict) -> None: 
        self.failure_rate = failure_rate
        self.readings_meta_data = readings_meta_data
        self.rand_num = random()

    @property
    def voltage(self) -> float | None: 
        if self.rand_num < self.failure_rate: 
            return None
        else: 
            i: int = next(i for i, meta in enumerate(self.readings_meta_data) if meta["name"] == "voltage")
            voltage_val = self.readings_meta_data[i]["min"] + random() * (self.readings_meta_data[i]["max"] - self.readings_meta_data[i]["min"])
            self.voltage_val = voltage_val
            return voltage_val


    @property
    def current(self) -> float | None: 
        if self.rand_num < self.failure_rate: 
            return None
        else: 
            i: int = next(i for i, meta in enumerate(self.readings_meta_data) if meta["name"] == "current")
            current_val = self.readings_meta_data[i]["min"] + random() * (self.readings_meta_data[i]["max"] - self.readings_meta_data[i]["min"])
            self.current_val = current_val; 
            return current_val

    # reset self.rand_num in temp setting to actually get the random number to change. Done by convetion in temp
    # because it is called second in the read function, keeping with the idea that current, voltage and 
    # power failure should be set by the same random number generator because they always fail 
    # together
    @property
    def power(self) -> float | None: 
        if self.rand_num < self.failure_rate: 
            self.rand_num = random()
            return None
        else: 
            self.rand_num = random()
            return self.current_val * self.voltage_val







        
