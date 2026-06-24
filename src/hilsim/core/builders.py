"""Build instances of actuators, sensors, and set up device connections"""

import importlib
import logging
from pathlib import Path

from hilsim.core.actuators import ActuatorBase
from hilsim.core.controls import (AdvancedCommunication, Controls,
                                      SerialInterface)
from hilsim.core.device_exceptions import DeviceConnectionError
from hilsim.core.i2c_bus import I2CBus
from hilsim.core.load_toml import LoadTOML
from hilsim.core.sensors import DriverBase, SensorBase
from hilsim.core.world_state import WorldState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------------------

class BuildComponents:
    """Build instances of actuators, sensors, and set up device connections"""

    def __init__(self, build_ctx: dict) -> None:
        self.sensor_config = build_ctx["sensor_config"]
        self.device_config = build_ctx["device_config"]
        self.actuator_config = build_ctx["actuator_config"]
        self.world_state = build_ctx["world_state"]
        self.i2c_bus = build_ctx["i2c_bus"]
        self.project_root = build_ctx["project_root"]
        self._auto_discover(
            self.project_root / "sensors"
        )  # Populates SensorBase.registry and DriverBase.Registry
        self._auto_discover(
            self.project_root / "actuators"
        )  # Populates ActuatorBase.registry

    def _auto_discover(self, directory: str) -> None:
        """Import all modules in a directory to trigger the __init_subclass__ registration"""
        path = Path(directory)
        for module_file in path.glob("*.py"):
            if module_file.name.startswith("_"):
                continue
            module_name = module_file.stem
            try:
                spec = importlib.util.spec_from_file_location(module_name, module_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception as e:
                raise ImportError(f"failed to load module '{module_file}': {e}") from e

    def _build_actuators(self) -> dict:
        """Create dictonary of instances of each actuator"""
        actuators = {}
        for name, config in self.actuator_config.items():
            driver_name = config["settings"]["driver"]
            driver_class = ActuatorBase.registry[driver_name]
            actuators[name] = driver_class(config, self.world_state, self.controller)

        return actuators

    def _build_fake_sensors_with_drivers(self):
        """Construct instances of drivers"""
        drivers = {}
        for sensor in self.sensor_config["sensor_params"]["enabled_sensors"]:

            # Query important parameters
            sensor_config = self.sensor_config["sensors"][sensor]
            fake_sensor_name = sensor_config["fake_sensor_name"]
            driver_name = sensor_config["driver_name"]

            # Create instance of fake sensor
            fake_sensor_class = SensorBase.registry[fake_sensor_name]
            fake_sensor = fake_sensor_class(sensor_config, self.world_state)

            # Create instance of driver
            driver_class = DriverBase.registry[driver_name]
            drivers[sensor] = driver_class(
                sensor, sensor_config, self.i2c_bus, fake_sensor
            )
            logger.info("Registered %s → %s", sensor, driver_class.__name__)

        return drivers

    def _build_devices(self) -> dict:
        """Build peripherial devices and open serial connections to them"""
        device_configs = self.device_config["devices"]
        advanced_comms_config = self.device_config["advanced_communication"]
        logger.info("building peripherial microcontrollers")

        device_dict = {}
        for device in self.device_config["enabled_devices"]:
            sub_config = device_configs[device]
            device_comms = SerialInterface(sub_config, device)
            device_w_advanced_comms = AdvancedCommunication(
                sub_config, advanced_comms_config, device_comms
            )
            connected = device_w_advanced_comms.device.connect()
            print(connected)
            if not connected:
                logger.error("Error connecting to %s", device)
                raise DeviceConnectionError(
                    device, "Failed to connect to device. See message logs."
                )
            logger.info("successfully connected to %s", device)
            device_dict[device] = device_w_advanced_comms
        return device_dict

    def build_all(self) -> dict:
        """Build all sensors, devices, and actuators"""
        self.controller = Controls(self._build_devices()) # actuators depend on the Controller!
        actuators = self._build_actuators()
        sensors = self._build_fake_sensors_with_drivers()
        return {"actuators": actuators, "sensors": sensors}


# ---------------------------------------------------------------------------------------