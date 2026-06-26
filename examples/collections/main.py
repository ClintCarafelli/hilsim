"""Main function"""

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
