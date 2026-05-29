"""Generate fake values for an INA260 sensor. Same methods as actual sensor"""

from random import random


class FakeINA260:
    """Fake INA260 that does not require physical hardware"""

    def __init__(self, config) -> None:
        self.config = config
        self.voltage_val = 0.0
        self.current_val = 0.0
        self.power_val = 0.0
        self.rand_num = 0.0
        self.counter = 0
        self.status: dict[str, str] = {}
        self.controls_running = False

    @property
    def voltage(self) -> float | None:
        """Generate voltage value"""
        if self._get_same_random() < self.config["failure_rate"]:
            raise ValueError("simulated failed reading")

        ps_V = self.config["base_states"]["power_supply"]["voltage"]
        self.voltage_val = ps_V + self._create_noise("base", "power_supply")
        return self.voltage_val

    @property
    def current(self) -> float:
        """Generate current value"""
        if self._get_same_random() < self.config["failure_rate"]:
            raise ValueError("simulated failed reading")
        if not self.controls_running:
            self.update_current()
        return self.current_val

    @property
    def power(self) -> float | None:
        "Generate power value"
        if self._get_same_random() < self.config["failure_rate"]:
            raise ValueError("simulated failed reading")
        return self.current_val * self.voltage_val

    def update_current(self, status: dict | None = None) -> None:
        """Take in hardware states and update expected current"""
        computer_current = self.config["base_states"]["computer"]["current"]
        current_output = computer_current + self._create_noise("base", "computer")
        if status is not None:
            self.status = status
        for hw_object, state in self.status.items():
            if state == "on":
                object_current = self.config["hardware_states"][hw_object]["on"]
                random_factor = self._create_noise("hardware", hw_object)
            else:
                object_current = 0
                random_factor = 0
            current_output = object_current + random_factor + current_output
        self.current_val = current_output

    def set_status(self, status:dict) -> None:
        """set the status (i.e. known hardware states)"""
        self.status = status

    # Same random should dictate failure of all three measurements because in practice
    # they all fail together
    def _get_same_random(self) -> float:
        """return the same random n times, here n=3"""
        # reset random number every 3 counts since this function gets called
        # three times for a full sensor read
        print(self.counter)
        if self.counter % 3 == 0:
            print("in here")
            self.counter += 1
            self.rand_num = random()
            return self.rand_num
        self.counter += 1
        return self.rand_num

    def _create_noise(self, category: str, hw_object: str) -> float:
        """Generate noise to reflect real hardware based on noise parameter"""
        if category == "base":
            noise_param = self.config["base_states"][hw_object]["noise"]
            noise_val = 2 * (noise_param * (random() - 0.5))
            return noise_val
        if category == "hardware":
            noise_param = self.config["hardware_states"][hw_object]["noise"]
            noise_val = 2 * (noise_param * (random() - 0.5))
            return noise_val
        return 0

