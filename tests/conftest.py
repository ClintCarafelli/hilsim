"""Set up fixtures for the whole test suite"""

import pytest


# The four major fixtures in this file mimic the four configuration toml files once
# loaded into dictonaries. They use arbitrary sensor names / parameters to 
# place an emphasis on the generlaity of the package. 


@pytest.fixture()
def sensor_config() -> dict:
    """Create a dictonary that mimics the sensor_config.toml"""
    return {
        "sensor_params": {"enabled_sensors": ["sensor_1", "sensor_2"], "sim_all": True, "skip_failed_init": True},
        "sensor_error_program": {
            "first_i2c_cycle": 4,
            "second_i2c_cycle": 5,
            "first_power_cycle": 6,
            "second_power_cycle": 7,
            "dead": 8,
        },
        "sensors": {
            "sensor_1": {
                "description": "reads variable_1 and variable_2",
                "num_measurements": 2,
                "driver_name": "Sensor1Driver",
                "fake_sensor_name": "FakeSensor1",
                "sim": True,
                "failure_rate": 0.0,
                "sim_fail_initialization": False,
                "readings": [
                    {
                        "name": "variable_1",
                        "units": "var_1_units",
                        "max": 100,
                        "min": 0,
                        "noise": 0,
                        "drift": 0.0,
                    },
                    {
                        "name": "variable_2",
                        "units": "var_2_units",
                        "max": 200,
                        "min": 50,
                        "noise": 0,
                        "drift": 0.0,
                    },
                ],
            },
            "sensor_2": {
                "description": "reads variable_3",
                "num_measurements": 1,
                "driver_name": "Sensor2Driver",
                "fake_sensor_name": "FakeSensor2",
                "sim": True,
                "failure_rate": 0.0,
                "sim_fail_initialization": False,
                "readings": [
                    {
                        "name": "variable_3",
                        "units": "var_3_units",
                        "max": 20,
                        "min": 10,
                        "noise": 0,
                        "drift": 0.0,
                    }
                ],
            },
        },
    }


@pytest.fixture
def actuator_config() -> dict:
    """Create a dictonary that mimics the actuator_config.toml"""
    return {
        "actuator_1": {
            "settings": {
                "name": "actuator_1",
                "driver": "Actuator1Driver",
                "device": "Device1",
                "pin": 6,
                "sim": True,
                "initial_state": "state_1",
                "states": ["state_1", "state_2"],
            },
            "failure_sim": {
                "stuck_probability": 0.0,
                "cta_latency": {"distribution": "normal", "mean": 20, "std": 3},
            },
            "effects": {
                "variable_1": {"effect_types": "s+t+p"},
                "variable_2": {"effect_types": "s"},
            },
        },
        "actuator_2": {
            "settings": {
                "name": "actuator_2",
                "driver": "Actuator2Driver",
                "device": "Device2",
                "pin": 7,
                "sim": True,
                "initial_state": "state_3",
                "states": ["state_3", "state_4"],
            },
            "failure_sim": {
                "stuck_probability": 0.0,
                "cta_latency": {"distribution": "uniform", "max": 5, "min": 30},
            },
            "effects": {
                "variable_1": {"effect_types": "s+t+p"},
                "variable_2": {"effect_types": "s"},
            },
        },
    }


@pytest.fixture
def device_config() -> dict:
    """Create a dictonary that mimics the device_config.toml"""
    return {
        "enabled_devices": ["device_1", "device_2"],
        "advanced_communication": {
            "retries": 3,
            "connection_cycles": 1,
            "power_cycles": 1,
        },
        "devices": {
            "device_1": {
                "sim": False,
                "super_sim": True,
                "super_sim_fr": 0.0,
                "baud_rate": 9600,
                "device_ID": "tty/ACM0",
                "fake_device_ID": "tmp/ttyVirtual0",
                "time_out": 1.0,
                "read_time": 0.5,
                "hb_send_msg": "ping",
                "hb_receive_msg": "pong",
            },
            "device_2": {
                "sim": False,
                "super_sim": True,
                "super_sim_fr": 0.0,
                "baud_rate": 9600,
                "device_ID": "tty/ACM1",
                "fake_device_ID": "tmp/ttyVirtual1",
                "time_out": 1.0,
                "read_time": 0.5,
                "hb_send_msg": "ping",
                "hb_receive_msg": "pong",
            },
        },
    }


@pytest.fixture
def world_state_config() -> dict:
    """Create a dictonary that mimics the world_state.toml"""
    return {
        "variables": {
            "variable_1": {"initial": 0.0, "units": "var_1_units"},
            "variable_2": {"initial": 15.0, "units": "var_2_units"},
            "variable_3": {"initial": 12.0, "units": "var_3_units"},
        }
    }
