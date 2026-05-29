from src.base_driver import BaseDriver, Reading
from src.SensorExceptions import SensorInitError, SensorReadError
from random import random
from src.fake_ina260 import FakeINA260

class INA260Driver(BaseDriver): 
    def __init__(self, sensor_id: str, config_dict: dict, i2c_bus: any, fake_sensor: FakeINA260) -> None: 
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim             = config_dict["sim"]
        self.failure_rate    = config_dict["failure_rate"]
        self.hardware_states = config_dict["hardware_states"]
        self.base_states     = config_dict["base_states"]
        self.fake_sensor     = fake_sensor

    def initialize(self) -> None: 
        """ Initialize the INA260 sensor """
        if self.sim: 
            self.device = self.fake_sensor
            self.initialized = True

        else: 
            try: 
                import adafruit_ina260
                self.device = adafruit_ina260.INA260(self.i2c_bus)
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
            raise SensorReadError(self.sensor_id, str(e)) from e
        
        return [Reading(m["name"], val, m["units"]) for val, m in zip(vals, self.readings_meta_data)]












        
