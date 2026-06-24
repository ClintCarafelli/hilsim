"""Drive the ME2 sensor, including initialize and read"""

from typing import Any
from random import random

from hilsim.core.world_state import WorldState
from hilsim.core.sensors import DriverBase, SensorBase

# If sim=False, the following will run: DFRobot_Oxygen import DFRobot_Oxygen_IIC


class FakeME2(SensorBase):
    """FAKE ME2 sensor. Contains same method as actual sensor code"""

    # Collection number isn't actually needed here since it is just used to average
    # samples from the real sensor. Nonetheless it must be an input to keep with the
    # method defined in DFRobot_Oxygen_IIC
    def get_oxygen_data(self, collection_number: int) -> float | None:
        self.add_failure_possibility()
        return self.get_return_value("O2")


class ME2Driver(DriverBase):
    """Drive the ME2 sensor, including initialize and read"""

    def __init__(
        self, sensor_id: str, config_dict: dict, i2c_bus: Any, fake_sensor: FakeME2
    ) -> None:
        super().__init__(sensor_id, config_dict, i2c_bus, fake_sensor)
        self.iic_mode = config_dict["IIC_mode"]
        self.i2c_address = config_dict["i2c_address"]
        self.collection_number = config_dict["collection_number"]
        self.sim_fail_initialization = config_dict["sim_fail_initialization"]

    def initialize_sim(self) -> None:
        self.device = self.fake_sensor

    def initialize_real(self) -> None:
        from DFRobot_Oxygen import DFRobot_Oxygen_IIC  # type: ignore[import-not-found]

        self.device = DFRobot_Oxygen_IIC(self.iic_mode, self.i2c_address)

    def form_vals_dict(self) -> dict:
        return {"O2": self.device.get_oxygen_data(self.collection_number)}
