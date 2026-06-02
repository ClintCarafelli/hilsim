"""Run and define the main 4-hour loop. Main entry point into the system"""
import os
import logging
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from src.LoadTOML import LoadTOML
from src.sensor_manager import SensorManager
from src.sensor_tracker import SensorTracker
from src.I2CBus import I2CBus
from src.file_manager import HandleLogging
from src.CreateFakeSensors import CreateFakeSensors

def main_loop(sm: SensorManager, st: SensorTracker, t: Table, c: Console) -> None:
    """ Run the software in the mainloop"""
    while True:
        #print("-"*30 + "Readings" + "-"*30)
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
        #print()
        st.track(data)
        time.sleep(2)


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
# Set up sensor configuration dictonary
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
    fake_sensors = CreateFakeSensors(sensor_config)

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
# Set up known hardware states
    status_dict = {"solenoid": "off",
                   "servo": "off",
                   "purple_lights": "on",
                   "white_lights": "off"}

    sensor_manager.sensors["INA260"].device.status = status_dict
#------------------------------------------------------------------------------
# Call the main loop
    while True:
        main_loop(sensor_manager, sensor_tracker, table, console)
#------------------------------------------------------------------------------
