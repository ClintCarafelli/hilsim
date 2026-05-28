from random import random

class FakeME2:
    def __init__(self,  config: dict) -> None:
        self.failure_rate       = config["failure_rate"]
        self.readings_meta_data = config["readings"]

    # Collection number isn't actually needed here since it is just used to average 
    # samples from the real sensor. Nonetheless it must be an input to keep with the 
    # method defined in DFRobot_Oxygen_IIC
    def get_oxygen_data(self, collection_number: int) -> float | None:
        if random() < self.failure_rate:
            raise Exception("simulated failed reading")
        else: 
            return self.readings_meta_data[0]["min"] + random() * self.readings_meta_data[0]["max"] - self.readings_meta_data[0]["min"]