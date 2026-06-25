"""Run and define the main 4-hour loop. Main entry point into the system"""

import time


#def convert_data_to_str_iterable(data: dict, time_val: float) -> list: 
#    """convert nested dictonaries of data for printing to rich table"""
#    data_row = []
#    for measurements in data.values(): 
#        for variable in measurements.values(): 
#            data_row.append(str(variable.value))
#    data_row.append(str(time_val))
#    return data_row


def main(ctx): 

    sensor_manager = ctx["sensor_manager"]
    sensor_tracker = ctx["sensor_tracker"]
    actuators      = ctx["actuators"]
    world_state    = ctx["world_state"]
    data_manager   = ctx["data_manager"]
    log_manager    = ctx["log_manager"]
    rich_table     = ctx["table"]
    console        = ctx["console"]


    opened = False
    closed = True
    injection_complete = False

    co2_solenoid = actuators["co2_solenoid"]

    start_time = time.time()

    while time.time() - start_time < 6: 
        now = time.time()
        data, time_val = sensor_manager.read_all()

        data_manager.add_data_to_file(data, time_val)
        rich_table.add_row(*data_manager.convert_data_to_str_iterable(data, time_val))
        console.print(rich_table)
        sensor_tracker.track(data)

        if now - start_time > 2 and not opened and not injection_complete:
            co2_solenoid.send_command("open")
            opened = True
            closed = False

        if world_state.get("CO2") > 1200 and not closed and not injection_complete:
            co2_solenoid.send_command("close")
            closed = True
            opened = False
            injection_complete = True

        time.sleep(0.2)
