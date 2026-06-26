"""main function"""

import time

def main(ctx):

    # Break up context
    sensor_manager = ctx["sensor_manager"]
    sensor_tracker = ctx["sensor_tracker"]
    actuators      = ctx["actuators"]
    world_state    = ctx["world_state"]
    data_manager   = ctx["data_manager"]
    log_manager    = ctx["log_manager"]
    rich_table     = ctx["table"]
    console        = ctx["console"]

    # Get instance of CO2 solenoid actuator
    co2_solenoid = actuators["Solenoid"]

    # create flag to terminate test
    test_complete = False
    start_terminal_clock = False
    open_command_sent = False
    close_command_sent = False

    while not test_complete:

        # Read sensor suite, add data to file, output to rich table, and track errors
        data, time_val = sensor_manager.read_all()
        data_manager.add_data_to_file(data, time_val)
        rich_table.add_row(*data_manager.convert_data_to_str_iterable(data, time_val))
        console.print(rich_table)
        sensor_tracker.track(data)

        # Pull CO2 data:
        CO2_data = data["SCD30"]["CO2"].value

        # Open solenoid when CO2 dips below 200 ppm, careful that
        # Readings can return none values
        if CO2_data is not None:
            if CO2_data < 200 and not open_command_sent:
                co2_solenoid.send_command("open")
                open_command_sent = True

            # Close solenoid when CO2 rises above 1200 ppm,
            # and terminate test 2 seconds later
            if CO2_data > 1200 and not close_command_sent:
                co2_solenoid.send_command("close")
                close_command_sent = True
                start_terminal_clock = True
                start_time = time.time()

            # Terminate 2 seconds after CO2 becomes greater than 1200 ppm
            if start_terminal_clock:
                if (time.time() - start_time) > 2:
                    test_complete = True

        # Sleep 0.2 seconds between sensor reads and logic evaluation
        time.sleep(0.2)



