"""Manage the sensor suite. Includes: initializing sensors and reading sensors"""

import time
import logging
from typing import Any

from hilsim.core.sensors import DriverBase, Reading
from hilsim.core.sensor_exceptions import SensorInitError, SensorReadError

logger = logging.getLogger(__name__)


class SensorManager:
    """This class manages the sensors suite, including:
    - mapping sensor drivers and fake sensors to enabled sensors in the config
    - initializing sensors
    - reading sensors
    """

    def __init__(
        self,
        config_dict: dict,
        i2c_bus: Any,
        sensor_drivers: dict,
        skip_failed_init: bool = False,
    ) -> None:
        self.skip_failed_init = skip_failed_init
        self.config_dict = config_dict
        self.i2c_bus = i2c_bus
        self.sensors = sensor_drivers

    def initialize_all(self) -> None:
        """Attempts to initialize all sensors listed in enabled_sensors in the config file"""
        failed: list[str] = []
        for sensor_id, sensor in self.sensors.items():
            try:
                logger.info("Initializing %s (%s)...", sensor_id, sensor.description)
                sensor.initialize()
                logger.info("Successful initialized %s", sensor_id)
            except SensorInitError as e:
                if self.skip_failed_init:
                    logger.critical("%s failed initialization: %s", sensor_id, e)
                    failed.append(sensor_id)
                else:
                    raise
        for sensor_id in failed:
            del self.sensors[sensor_id]

    def read_all(self) -> tuple[dict[str, list[Reading]], float]:
        """Reads all sensors that were successfully initailized"""

        results: dict[str, dict[str, Reading]] = {}
        for sensor_id, sensor in self.sensors.items():
            print(sensor_id)
            print(sensor)
            if not sensor.initialized:
                logger.warning("Skipping %s : not initialized", sensor_id)
                results[sensor_id] = self._build_None_reading(sensor_id)
                continue
            try:
                logger.info("Reading %s...", sensor_id)
                results[sensor_id] = sensor.read()
                print(results)
            except SensorReadError as e:
                logger.error("Sensor reading failed for %s, %s", sensor_id, e)
                results[sensor_id] = self._build_None_reading(sensor_id)

        return results, time.time()

    def initialize(self, sensor_id: str) -> None:
        """Initializes just one sensor specified by the sensor_id"""
        if sensor_id not in self.sensors:
            logger.error("%s is not an available sensor", sensor_id)
            raise SensorInitError(sensor_id, "this is not an available sensor.")
        try:
            logger.info(
                "Initializing %s (%s)...",
                sensor_id,
                self.sensors[sensor_id].description,
            )
            self.sensors[sensor_id].initialize()
            logger.info("Successfully initialized %s...", sensor_id)
        except SensorInitError as e:
            logger.critical("Initialization failed for %s, %s", sensor_id, e)
            if not self.skip_failed_init:
                raise

    def read(self, sensor_id: str) -> tuple[dict[str, dict[str, Reading]], float]:
        """Reads just one sensor specified by its sensor_id"""

        results: dict[str, dict[str,Reading]] = {}
        if sensor_id not in self.sensors:
            logger.critical("%s is not an available sensor", sensor_id)
            msg =  "not an available sensor. Does not match a sensor in config.toml"
            raise SensorReadError(sensor_id, msg)
        try:
            logger.info("Reading %s...", sensor_id)
            results[sensor_id] = self.sensors[sensor_id].read()
        except SensorReadError as e:
            logger.error("Sensor reading failed for %s, %s", sensor_id, e)
            results[sensor_id] = self._build_None_reading(sensor_id)

        return results, time.time()
    
    def _build_None_reading(self, sensor_id: str) -> dict[str, Reading]: 
        """Build a None reading for a failed sensor read"""
        rmd_name_map = self._map_readings_to_name(sensor_id)
        failed_readings_dict = {}
        for key, params in rmd_name_map.items(): 
            failed_readings_dict[key] = Reading(None, params["units"])
        return failed_readings_dict

    def _map_readings_to_name(self, sensor_id: str) -> dict[str, dict]:
        """map readings list of dictonaries to names"""
        rmd_name_map: dict[str, dict] = {}
        for reading in self.config_dict["sensors"][sensor_id]["readings"]:
            rmd_name_map[reading["name"]] = reading
        return rmd_name_map

    def build_header(self, sample_data: dict) -> list[list[str]]:
        """Creates a header for a csv file based on a reading"""
        sensor_id_list = []
        variable_list = []
        for sensor_id, measurements in sample_data.items(): 
            sensor_id_list.extend([sensor_id] * len(measurements))
            for variable, reading in measurements.items(): 
                variable_list.append(variable + " (" + reading.unit + ")")

        sensor_id_list.append("system_clock")
        variable_list.append("time (UNIX)")
        return [sensor_id_list, variable_list]
