import importlib
import logging
import threading
import time
from pathlib import Path
from typing import Any

from hilsim.core.builders import BuildComponents
from hilsim.core.file_manager import DataManager, LogManager
from hilsim.core.i2c_bus import I2CBus
from hilsim.core.load_toml import LoadTOML
from hilsim.core.sensor_manager import SensorManager
from hilsim.core.sensor_tracker import SensorTracker
from hilsim.core.world_state import WorldState
from rich.console import Console
from rich.table import Table


def build_context(root: Path) -> dict:
    """Create context to build hardware"""

    # Get configruations
    world_state_config = LoadTOML(root / "world_state.toml")
    device_config = LoadTOML(root / "device_config.toml")
    actuator_config = LoadTOML(root / "actuator_config.toml")
    sensor_config = LoadTOML(root / "sensor_config.toml")

    # Create world_state
    world_state = WorldState(world_state_config)

    # Set up I2C bus
    sim_all_sensors = sensor_config["sensor_params"]["sim_all"]

    I2C_Handler = I2CBus(sim_all_sensors)
    i2c_bus = I2C_Handler.initialize_i2c_bus()

    build_ctx = {
        "sensor_config": sensor_config,
        "device_config": device_config,
        "actuator_config": actuator_config,
        "world_state": world_state,
        "i2c_bus": i2c_bus,
        "project_root": root,
    }
    return build_ctx


def build_hardware(build_ctx: dict) -> tuple[dict, dict]:
    """Construct sensor and actuator instances. This includes creating
    connections to devices"""
    builder = BuildComponents(build_ctx)
    hardware = builder.build_all()
    return hardware["sensors"], hardware["actuators"]


def build_sensor_stack(
    sensor_config: dict, i2c_bus: Any, sensor_drivers: dict
) -> tuple:
    """Initialize sensor manager and sensor tracker"""
    sensor_manager = SensorManager(sensor_config, i2c_bus, sensor_drivers, True)
    sensor_tracker = SensorTracker(sensor_config)
    sensor_manager.initialize_all()
    return sensor_manager, sensor_tracker


def build_table(sensor_manager: SensorManager) -> tuple[Table, list, list]:
    """Build the rich display table and return"""
    # Set up rich output for terminal data table
    sample_data, _ = sensor_manager.read_all()
    headers = sensor_manager.build_header(sample_data)
    top_header = headers[0]
    bottom_header = headers[1]

    table = Table(
        title="Sensor Readings",
        show_header=False,
    )
    table.add_row(*top_header)
    table.add_row(*bottom_header)
    table.add_section()
    return table, top_header, bottom_header

def import_user_main(project_path: Path): 
    """Import the main module that contains the developer's main function"""
    spec = importlib.util.spec_from_file_location("main", project_path / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def background_dynamics(world_state: WorldState, actuators: dict) -> None:
    """Create the background dynamics of the system"""
    start_time = time.time()
    last_time = start_time
    try:
        while True:
            now = time.time()
            dt = now - last_time
            last_time = now

            for actuator in actuators.values():
                actuator.update(dt)

            world_state.update_state()

            time.sleep(0.005)  # About as fast as you're gonna get
    except Exception as e:
        print(e)


def run(root: Path) -> None:
    """Main entry point"""
    log_manager = LogManager()
    log_manager.start_logging()

    build_ctx = build_context(root)
    sensor_drivers, actuators = build_hardware(build_ctx)

    sensor_manager, sensor_tracker = build_sensor_stack(
        build_ctx["sensor_config"],
        build_ctx["i2c_bus"],
        sensor_drivers,
    )

    rich_table, top_header, bottom_header = build_table(sensor_manager)
    data_manager = DataManager(Path("data"), [top_header, bottom_header])

    ctx = {
        "sensor_manager": sensor_manager,
        "sensor_tracker": sensor_tracker,
        "actuators": actuators,
        "world_state": build_ctx["world_state"],
        "data_manager": data_manager,
        "log_manager": log_manager,
        "table": rich_table,
        "console": Console()
    }

    bdt = threading.Thread(
        target=background_dynamics,
        args=(build_ctx["world_state"], actuators),
        daemon=True,
    )
    bdt.start()

    user_main = import_user_main(root)
    user_main.main(ctx)


if __name__ == "__main__":
    run(Path.cwd())
