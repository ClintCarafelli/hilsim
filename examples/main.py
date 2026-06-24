"""Run and define the main 4-hour loop. Main entry point into the system"""

import time

from rich.console import Console
from rich.table import Table


def main(ctx): 

    sensor_manager = ctx["sensor_manager"]
    sensor_tracker = ctx["sensor_tracker"]
    actuators      = ctx["actuators"]
    world_state    = ctx["world_state"]
    data_manager   = ctx["data_manager"]
    log_manager    = ctx["log_manager"]

    sample_data, _ = sensor_manager.read_all()
    headers = sensor_manager.build_header(sample_data)
    top_header = headers[0]
    top_header.append("system clock")
    bottom_header = headers[1]
    bottom_header.append("time (UNIX)")

    console = Console()
    table = Table(title="Sensor Readings", show_header=False,)
    table.add_row(*top_header)
    table.add_row(*bottom_header)
    table.add_section()

    opened = False
    closed = True
    injection_complete = False

    co2_solenoid = actuators["co2_solenoid"]

    start_time = time.time()

    while True: 
        now = time.time()
        data, time_val = sensor_manager.read_all()


        data_manager.add_data_to_file(data, time_val)
        #table.add_row(*data_row)
        #console.print(table)
        sensor_tracker.track(data)

        if now - start_time > 1 and not opened and not injection_complete:
            co2_solenoid.send_command("open")
            opened = True
            closed = False

        if world_state.get("CO2") > 1200 and not closed and not injection_complete:
            co2_solenoid.send_command("close")
            closed = True
            opened = False
            injection_complete = True


        time.sleep(0.5)
