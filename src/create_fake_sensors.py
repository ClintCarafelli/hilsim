from src.registries import fake_sensor_registry

class CreateFakeSensors:
    def __init__(self, config: dict) -> None: 
        self.config  = config
        self.sensors = {}
        self._build_fake_sensors()

    def _build_fake_sensors(self):
        for sensor in self.config["sensor_params"]["enabled_sensors"]:
            sensor_class = fake_sensor_registry[sensor]
            self.sensors[sensor] = sensor_class(self.config["sensors"][sensor])