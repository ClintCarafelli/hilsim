from src.BaseSensor import Reading, BaseSensor
from src.SensorExceptions import SensorInitError, SensorReadError
from random import random
# If sim=False, the following will run: DFRobot_Oxygen import DFRobot_Oxygen_IIC

class ME2Driver(BaseSensor):

    def __init__(self, sensor_id: str, config_dict: dict, i2c_bus: any) -> None:
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim = config_dict["sim"]
        self.failure_rate = config_dict["failure_rate"]
        self.IIC_mode = config_dict["IIC_mode"]
        self.i2c_address = config_dict["i2c_address"]
        self.collection_number = config_dict["collection_number"]


    def initialize(self):
        """Initialize the ME2 (DFRobot) oxygen sensor"""
        if self.sim:
            self.device = FakeME2(self.failure_rate, self.readings_meta_data)
            self.initialized = True

        else: 
            try: 
                from DFRobot_Oxygen import DFRobot_Oxygen_IIC
                self.device = DFRobot_Oxygen_IIC(self.IIC_mode, self.i2c_address)
                self.initialized = True

            except Exception as e: 
                raise SensorInitError(self.sensor_id, str(e)) from e
            
    def read(self):

        if not self.initialized:
            raise SensorReadError(self.sensor_id, "Sensor not initialized")
        try: 
            vals = self.device.get_oxygen_data(self.collection_number)

        except Exception as e: 
            vals = None
            raise SensorReadError(self.sensor_id, str(e)) from e
        
        return [Reading(self.readings_meta_data[0]["name"], vals, self.readings_meta_data[0]["units"])]
    

class FakeME2:

    def __init__(self, failure_rate: float, readings_meta_data: dict) -> None:
        self.failure_rate = failure_rate
        self.readings_meta_data = readings_meta_data

    # Collection number isn't actually needed here since it is just used to average 
    # samples from the real sensor. Nonetheless it must be an input to keep with the 
    # method defined in DFRobot_Oxygen_IIC
    def get_oxygen_data(self, collection_number: int) -> float | None:
        if random() < self.failure_rate:
            return None
        else: 
            return self.readings_meta_data[0]["min"] + random() * self.readings_meta_data[0]["max"] - self.readings_meta_data[0]["min"]