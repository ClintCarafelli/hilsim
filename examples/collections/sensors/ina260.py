"""Anything related to the ina260 sensor"""

from hilsim.core.sensors import DriverBase, SensorBase
from hilsim.core.world_state import WorldState

class FakeINA260(SensorBase):
    """Fake INA260 that does not require physical hardware"""

    def __init__(self, config: dict, world_state: WorldState) -> None:
        super().__init__(config, world_state)
        self.voltage_val = 0.0
        self.current_val = 0.0

    @property
    def voltage(self) -> float | None:
        """Generate voltage value"""
        self.add_failure_possibility()
        self.voltage_val = self.get_return_value("system_voltage")
        return self.voltage_val 

    @property
    def current(self) -> float:
        """Generate current value"""
        self.add_failure_possibility()
        self.current_val = self.get_return_value("system_current")
        return self.current_val

    @property
    def power(self) -> float | None:
        "Generate power value"
        self.add_failure_possibility()
        return self.current_val * self.voltage_val

class INA260Driver(DriverBase):
    """Driver for INA260 sensor, standardizes sensor to initialize() and read()"""

    def initialize_sim(self) -> None:
        self.device = self.fake_sensor
        
    def initialize_real(self) -> None:
        import adafruit_ina260  # type: ignore[import-not-found]
        self.device = adafruit_ina260.INA260(self.i2c_bus)

    def form_vals_dict(self) -> dict: 
        voltage = self.device.voltage
        current = self.device.current
        power = self.device.power
        return {"system_voltage": voltage, 
                "system_current": current, 
                "system_power": power}