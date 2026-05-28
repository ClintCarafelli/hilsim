from random import random
class FakeBMP388: 
    def __init__(self, config) -> None:
        self.failure_rate       = config["failure_rate"]
        self.readings_meta_data = config["readings"]
        self.counter            = 0
        self.rand_num           = 0.5

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
