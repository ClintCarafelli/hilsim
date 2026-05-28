import logging
from src.BaseSensor import Reading, BaseSensor
from src.SensorExceptions import SensorInitError, SensorReadError, ConfigError
from  src.DriverRegistry import driver_registry

logger = logging.getLogger(__name__)

class SensorManager:
    """ This class manages the sensors suite"""

    def __init__(self, config_dict: dict, i2c_bus: any, fake_sensors: dict, skip_failed_init: bool = False) -> None:
        self.skip_failed_init                = skip_failed_init
        self.config_dict                     = config_dict
        self._sensors: dict[str, BaseSensor] = {}
        self.i2c_bus                         = i2c_bus
        self.fake_sensors                    = fake_sensors
        self._build_sensors()

    def _build_sensors(self) -> None: 
        """ Just maps the self._sensors[sensor_id] to the driver class so that 
        the sensors functions can be called self._sensors[sensor_id]
         by way of example: you can do self._sensors[sensor_id].read() """
        
        self.enabled_sensors: list[dict] = self.config_dict['sensor_params'].get("enabled_sensors", [])
        all_sensor_configs: dict         = self.config_dict.get("sensors", {})

        if not self.enabled_sensors:
            raise ConfigError("all_sensors", "You have no enabled sensors " + 
                "(i.e. the enabled_sensors list in sensors_config.toml is empty.)" +
                "running this code with no sensors is vacuous.")
        for sensor_id in self.enabled_sensors:
            if sensor_id not in all_sensor_configs.keys():
                 raise ConfigError("enabled_sensors sensor_config.toml mismatch", 
                    f"{sensor_id} is in 'enabled_sensors' but has no " +
                    f"[sensors.{sensor_id}] block in the config.")
            
            sensor_config = all_sensor_configs[sensor_id]
            driver_name = sensor_config.get("driver", [])
    
            if not driver_name:
                raise ConfigError(sensor_id, "missing 'driver' in sensor_config.toml file.")
            
            if driver_name not in driver_registry:
                raise ConfigError(sensor_id, f"Unknown driver name {driver_name!r} for {sensor_id!r}. " 
                    f"Registered drivers: {list(driver_registry)}")
            
            driver_class = driver_registry[driver_name]
            fake_sensor = self.fake_sensors[sensor_id]
            self._sensors[sensor_id] = driver_class(sensor_id, sensor_config, self.i2c_bus, fake_sensor)
            logger.info("Registered %s → %s", sensor_id, driver_class.__name__)
            
    def initialize_all(self) -> None: 
        failed = []
        for sensor_id, sensor in self._sensors.items():
            try: 
                logger.info("Initializing %s (%s)...", sensor_id, sensor.description)
                sensor.initialize()
                logger.info("Successful initialized %s", sensor_id)
            except Exception as e: 
                if self.skip_failed_init:
                    logger.critical("%s failed initialization: %s", sensor_id, e)
                    failed.append(sensor_id)
                else: 
                    raise SensorInitError(f"{sensor_id}", f"failed initialization: {e}")
        for sensor_id in failed:
            del self._sensors[sensor_id]

    def read_all(self) -> dict[str, list[Reading]]:
        """Reads all sensors that were orginally initailized"""

        results: dict[str, list[Reading]] = {}
        for sensor_id, sensor in self._sensors.items():
            if not sensor.initialized:
                logger.warning("Skipping %s : not initialized", sensor_id)
                results[sensor_id] = [Reading(None, None, None)] * self.config_dict["sensors"][sensor_id]["num_measurements"]
                continue 
            try: 
                logger.info("Reading %s...", sensor_id)
                results[sensor_id] = sensor.read()
            except Exception as e: 
                logger.error("Sensor reading failed for %s, %s", sensor_id, e)
                results[sensor_id] = [Reading(None, None, None)] * self.config_dict["sensors"][sensor_id]["num_measurements"]
        return results
    
    def initialize(self, sensor_id: str) -> None:
        """ Initializes just one sensor specified by the sensor_id"""
        if sensor_id not in self._sensors:
            logger.error("%s is not an available sensor", sensor_id)
            raise SensorInitError(sensor_id, "this is not an available sensor.")
        try: 
            logger.info("Initializing %s (%s)...", sensor_id, self._sensors[sensor_id].description)
            self._sensors[sensor_id].initialize()
            logger.info("Successfully initialized %s...", sensor_id)
        except Exception as e: 
            logger.critical("Initialization failed for %s, %s", sensor_id, e)
            if not self.skip_failed_init:
                raise SensorInitError(f"{sensor_id}", f"failed initialization: {e}")

    def read(self, sensor_id: str) -> list[Reading]:
        """ Reads just one sensor specified by its sensor_id"""

        results: dict[str, list[Reading]] = {}
        if sensor_id not in self._sensors:
            logger.critical("%s is not an available sensor", sensor_id)
            raise SensorReadError(sensor_id, "not an available sensor. Does not match a sensor in config.toml" )
        else:
            try: 
                logger.info("Reading %s...", sensor_id)
                results[sensor_id] = self._sensors[sensor_id].read()
            except Exception as e: 
                logger.error("Sensor reading failed for %s, %s", sensor_id, e)
                results[sensor_id] = [Reading(None, None, None)] * self.config_dict["sensors"][sensor_id]["num_measurements"]
        return results
            

             



            


            



