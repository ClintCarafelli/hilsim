"""Drive the ME2 sensor, including initialize and read"""
from typing import Any
from src.base_driver import Reading, BaseDriver
from src.SensorExceptions import SensorInitError, SensorReadError
from src.fake_me2 import FakeME2

# If sim=False, the following will run: DFRobot_Oxygen import DFRobot_Oxygen_IIC


class ME2Driver(BaseDriver):
    """Drive the ME2 sensor, including initialize and read"""
    def __init__(
        self, sensor_id: str, config_dict: dict, i2c_bus: Any, fake_sensor: FakeME2
    ) -> None:
        super().__init__(sensor_id, config_dict, i2c_bus)
        self.sim = config_dict["sim"]
        self.iic_mode = config_dict["IIC_mode"]
        self.i2c_address = config_dict["i2c_address"]
        self.collection_number = config_dict["collection_number"]
        self.sim_fail_initialization = config_dict["sim_fail_initialization"]
        self.fake_sensor = fake_sensor
        self.device = None
        self.sensor_id = sensor_id

    def initialize(self) -> None:
        """Initialize the ME2 (DFRobot) oxygen sensor"""
        try:
            if self.sim:
                if self.sim_fail_initialization:
                    raise SensorInitError(
                        self.sensor_id, "simulate failed initialization"
                    )
                self.device = self.fake_sensor
                self.initialized = True
            else:
                from DFRobot_Oxygen import DFRobot_Oxygen_IIC

                self.device = DFRobot_Oxygen_IIC(self.iic_mode, self.i2c_address)
                self.initialized = True
        except Exception as e:
            raise SensorInitError(self.sensor_id, str(e)) from e

    def read(self) -> list[Reading]:
        if not self.initialized:
            raise SensorReadError(self.sensor_id, "Sensor not initialized")
        try:
            vals = self.device.get_oxygen_data(self.collection_number)

        except Exception as e:
            raise SensorReadError(self.sensor_id, str(e)) from e

        return [
            Reading(
                self.readings_meta_data[0]["name"],
                vals,
                self.readings_meta_data[0]["units"],
            )
        ]
