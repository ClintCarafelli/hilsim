import logging
from BaseSensor import Reading, BaseSensor, driver_registry
from SensorExceptions import SensorInitError, SensorReadError, ConfigError, ConfigErrorHandler
 
logger = logging.getLogger(__name__)

class SensorManager:
    """ This class manages the sensors suite"""

    def __init__(self, config_dict: dict, i2c_bus: any, skip_failed_init: bool = False) -> None:
        self.skip_failed_init = skip_failed_init
        self.config_dict = config_dict
        self._sensors: dict[str, BaseSensor] = {}
        self.i2c_bus = i2c_bus
        self._build_sensors(config_dict)
        self.dead_sensors: bool = dict.fromkeys(self.config_dict["sensor_params"].get("enabled_sensors", []), False)

    def initialize_all(self) -> None: 
        failed = []
        for sensor_id, sensor in self._sensors.items():
            try: 
                logger.info("Initializing %s (%s)...", sensor_id, sensor.description)
                sensor.initialize()
                logger.info("Successful initialized %s", sensor_id)
            except SensorInitError as e: 
                logger.warning("%s failed initialization: %s", sensor_id, e)
                failed.append(sensor_id)
        for sensor_id in failed:
            del self._sensors[sensor_id]


    def read_all(self) -> dict[str, list[Reading]]:
        """Reads all senors that were orginally initailized"""

        results: dict[str, list[Reading]] = {}
        for sensor_id, sensor in self._sensors.items():
            if not sensor.initialized:
                logger.warning("Skipping %s : not initialized", sensor_id)
                results[sensor_id] = []
                continue 
            try: 
                logger.info("Reading %s...", sensor_id)
                results[sensor_id] = sensor.read()
            except SensorReadError as e: 
                logger.error("Sensor reading failed for %s, %s", sensor_id, e)
                results[sensor_id] = []
        return results
    

    def read(self, sensor_id: str) -> list[Reading]:
        """ Reads just one sensor specified by its sensor_id"""

        results: dict[str, list[Reading]] = {}
        if sensor_id not in self._sensors:
            logger.error("%s is not an available sensor", sensor_id)
            results[sensor_id] = []
        else:
            try: 
                results[sensor_id] = self._sensors[sensor_id].read()
            except SensorReadError as e: 
                logger.error("Sensor reading failed for %s, %s", sensor_id, e)
                results[sensor_id] = []
        return results
    

    def initialize(self, sensor_id: str) -> None:
        """ Initializes just one sensor specified by the sensor_id"""

        if sensor_id not in self._sensors:
            logger.error("%s is not an available sensor", sensor_id)
        else:
            try: 
                logger.info("Initializing %s (%s)...", sensor_id, self._sensors[sensor_id].description)
                self._sensors[sensor_id].initialize()
                logger.info("Successfully initialized %s...", sensor_id)
            except SensorInitError as e: 
                logger.error("Initialization failed for %s, s", sensor_id, e)


    def _build_sensors(self, config_dict: dict) -> None: 
        """ Just maps the self._sensors[sensor_id] to the driver class so that 
        the sensors functions can be called self._sensors[sensor_id]
         by way of example: you can do self._sensors[sensor_id].read() """
    
        enabled: list[str] = config_dict['sensor_params'].get("enabled_sensors", [])
        self.enabled_sensors = enabled
        all_sensor_configs: dict = config_dict.get("sensors", {})

        if not enabled:
            logger.warning("'enabled_sensors' is empty in the config.toml file. No sensors will run.")

        for sensor_id in enabled: 
            if sensor_id not in all_sensor_configs:
                 raise ConfigError(f"{sensor_id!r} is in 'enabled_sensors' but has no " 
                    f"[sensors.{sensor_id}] block in the config.")
            
            sensor_config = all_sensor_configs[sensor_id]
            driver_name = sensor_config.get("driver", [])

            if not driver_name:
                raise ConfigError(sensor_id, "missing 'driver' in config.toml file.")
            
            if driver_name not in driver_registry:
                raise ConfigError(sensor_id, f"Unknown driver name {driver_name!r} for {sensor_id!r}. " 
                    f"Registered drivers: {list(driver_registry)}")
            
            driver_class = driver_registry[driver_name]
            self._sensors[sensor_id] = driver_class(sensor_id, sensor_config, self.i2c_bus)
            logger.info("Registered %s → %s", sensor_id, driver_class.__name__)

            


            



