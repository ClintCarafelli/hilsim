from random import random

class FakeSTEMMA:
    """ Provides a fake device / methods for the Steamma soil moisture sensor"""
    def __init__(self, config) -> None:
        self.failure_rate       = config["failure_rate"]
        self.readings_meta_data = config["readings"]
        self.counter            = 0
        self.rand_num           = 0

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

