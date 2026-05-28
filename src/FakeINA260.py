from random import random

class FakeINA260:
    def __init__(self, config) -> None: 
        self.failure_rate       = config["failure_rate"]
        self.readings_meta_data = config["readings"]
        self.hardware_states    = config["hardware_states"]
        self.base_states        = config["base_states"]
        self.voltage_val        = 0
        self.current_val        = 0
        self.power_val          = 0
        self.rand_num           = 0
        self.counter            = 0
        self.status             = {}
        self.controls_running   = False 

    @property
    def voltage(self) -> float | None: 
        if self._get_same_random() < self.failure_rate: 
            raise Exception("simulated failed reading")
        
        self.voltage_val = self.base_states["power_supply"]["voltage"] + self._create_noise("base", "power_supply")
        return self.voltage_val

    @property
    def current(self) -> float | None: 
        if self._get_same_random() < self.failure_rate: 
            raise Exception("simulated failed reading")
        if not self.controls_running:
            self._update_current()
        return self.current_val
        
    @property
    def power(self) -> float | None: 
        if self._get_same_random() < self.failure_rate: 
            raise Exception("simulated failed reading")
        else: 
            if self.current_val is None or self.voltage_val is None: 
                return None
            return self.current_val * self.voltage_val
        
    def _update_current(self, status: dict | None = None) -> None: 
        """ Take in hardware states and update expected current"""
        current_output = self.base_states["computer"]["current"] + self._create_noise("base", "computer")
        print("CURRENT OUTPUT")
        print(current_output)
        if status is not None: 
            self.status = status
        for object, state in self.status.items():
            if state == "on":
                object_current = self.hardware_states[object]["on"]
                random_factor  = self._create_noise("hardware", object)
            else: 
                object_current = 0
                random_factor  = 0
            current_output = object_current + random_factor + current_output
        self.current_val = current_output
    
    # When these sensors are actually implimented, they never fail on a single parameter read, 
    # rather they all fail together (likey due to impedance / emi on the data lines leading to an 
    # unrecognizable i2c address and therefore a failed reading for all parameters. Hence I
    # have tied the failure of indivdual parameters together by making the random number that
    # dictates failure only reset after both functions are called (they are never called in isolation))
    def _get_same_random(self) -> float:
        # reset random number every 3 counts since this function gets called twice for a full sensor read
        self.counter += 1
        if self.counter % 3 == 0:
            self.rand_num = random()
            return self.rand_num
        else: 
            return self.rand_num
        
    def _create_noise(self, category: str, object: str) -> float: 
        """ create a random number scaled by "noise" value in config file, 
        using a continuous uniform distribution with range [-0.5, 0.5]"""
        if category == "base":
            return 2 * self.base_states[object]["noise"] * (random() - 0.5)

        if category == "hardware":
            return 2 * self.hardware_states[object]["noise"] * (random() - 0.5)

