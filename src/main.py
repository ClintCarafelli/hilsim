"""Run and define the main 4-hour loop. Main entry point into the system"""
import os
import logging
import time
import pprint
from pathlib import Path
from rich.console import Console
from rich.table import Table
from src.load_toml import LoadTOML
from src.world_state import WorldState
from src.sensor_manager import SensorManager
from src.sensor_tracker import SensorTracker
from src.i2c_bus import I2CBus
from src.actuators import build_actuators
from src.file_manager import HandleLogging
from src.create_fake_sensors import CreateFakeSensors
from src.controls import Controls, build_peripherial_devices
from src.co2_solenoid import CO2Solenoid

def main_loop(sm: SensorManager, st: SensorTracker, t: Table, c: Console, controls: Controls, actuators: dict) -> None:
    """ Run the software in the mainloop"""

    start_time = time.time()
    last_time = start_time

    opened = False
    closed = True
    injection_complete = False

    co2_solenoid = actuators["co2_solenoid"]



    while True:
        now = time.time()
        dt = now - last_time
        last_time = now
    
        data = sm.read_all()
        data_row = []
        for _, readings in data.items():
            if readings:
                for r in readings:
                    if r.value is None:
                        data_row.append("NONE")
                        #print("NONE: NONE NONE")
                    else:
                        data_row.append(str(round(r.value, 2)))
                        #print(r.name + " " +  str(r.value) +  " " +  str(r.unit))
            else:
                print("NO DATA")
        data_row.append(str(round(time.time(), 2)))

        t.add_row(*data_row)
        c.print(t)
        st.track(data)

        if now - start_time > 1 and not opened and not injection_complete:
            co2_solenoid.send_command("open")
            opened = True
            closed = False

        if world_state.get("CO2") > 1200 and not closed and not injection_complete:
            co2_solenoid.send_command("close")
            closed = True
            opened = False
            injection_complete = True


        co2_solenoid.update(dt)
        world_state.update_state()

        time.sleep(0.01)


if __name__ == "__main__":
#------------------------------------------------------------------------------
# Set up constants / parameters
    PCA = True

#------------------------------------------------------------------------------
# Set up Logging
    log_file_manager = HandleLogging()
    log_file_manager.start_logging()
    logger = logging.getLogger(__name__)

#------------------------------------------------------------------------------
# Set up world state
    world_state_config_path = Path(__file__).parent.parent / "world_state.toml"
    world_state_config = LoadTOML(world_state_config_path)

    world_state = WorldState(world_state_config)

#------------------------------------------------------------------------------
# Set up controller
    controls_config_path = Path(__file__).parent.parent / "device_config.toml"
    controls_config = LoadTOML(controls_config_path)

    device_map = build_peripherial_devices(controls_config)
    controller = Controls(device_map)

#------------------------------------------------------------------------------
# set up actuators
    actuator_config_path = Path(__file__).parent.parent / "actuator_config.toml"
    actuator_config = LoadTOML(actuator_config_path)

    actuators = build_actuators(actuator_config, world_state, controller)

#------------------------------------------------------------------------------
# Set up sensor configuration
    sensor_config_path = Path(__file__).parent.parent / "sensor_config.toml"
    sensor_config = LoadTOML(sensor_config_path)
    sensor_config["main_path"] = os.path.dirname(os.path.abspath(__file__))

#------------------------------------------------------------------------------
# Set up I2C bus
    sim_all_sensors = sensor_config["sensor_params"]["sim_all"]
    I2C_Handler = I2CBus(sim_all_sensors)
    i2c_bus = I2C_Handler.initialize_i2c_bus()


#------------------------------------------------------------------------------
# Set up fake sensors:
    fake_sensors = CreateFakeSensors(sensor_config, world_state)

#------------------------------------------------------------------------------
# set up sensor managing and tracking
    sensor_manager = SensorManager(sensor_config,
                                   i2c_bus,
                                   fake_sensors.sensors,
                                   True)
    sensor_manager.initialize_all()
    sensor_tracker = SensorTracker(sensor_config)

#------------------------------------------------------------------------------
# Set up rich output for terminal data table
    header_list = sensor_manager.build_header()
    header_list.append("time (UNIX)")
    console = Console()
    table = Table(title="Sensor Readings")
    for header in header_list:
        table.add_column(header)

#------------------------------------------------------------------------------
# Call the main loop
    while True:
        main_loop(sensor_manager, 
                  sensor_tracker, 
                  table, 
                  console, 
                  controller, 
                  actuators)
#------------------------------------------------------------------------------
