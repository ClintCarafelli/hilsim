from src.registries import fake_sensor_registry
from src.world_state import WorldState

class CreateFakeSensors:
    def __init__(self, config: dict, world_state: WorldState) -> None: 
        self.config  = config
        self.sensors = {}
        self.world_state = world_state
        self._build_fake_sensors()

    def _build_fake_sensors(self):
        for sensor in self.config["sensor_params"]["enabled_sensors"]:
            sensor_class = fake_sensor_registry[sensor]
            self.sensors[sensor] = sensor_class(self.config["sensors"][sensor], self.world_state)