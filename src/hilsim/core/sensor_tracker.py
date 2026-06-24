"""Contains SensorTracker class, used for tracking errors on sensors"""

import logging
import operator
from collections.abc import Callable

logger = logging.getLogger(__name__)


class SensorTracker:
    """Track subsequent errors on sensors and return mitigation techniques"""

    def __init__(self, config_dict: dict) -> None:
        enabled_sensors = config_dict["sensor_params"].get("enabled_sensors", [])

        self.dead_sensors: dict[str, bool] = dict.fromkeys(enabled_sensors, False)
        self.sensor_errors: dict[str, int] = dict.fromkeys(enabled_sensors, 0)
        self.sensor_error_sol: dict[str, bool] = {
            "i2c_cycle": False,
            "power_cycle": False,
        }

        self.first_i2c_cycle_trig = config_dict["sensor_error_program"][
            "first_i2c_cycle"
        ]
        self.second_i2c_cycle_trig = config_dict["sensor_error_program"][
            "second_i2c_cycle"
        ]
        self.first_power_cycle_trig = config_dict["sensor_error_program"][
            "first_power_cycle"
        ]
        self.second_power_cycle_trig = config_dict["sensor_error_program"][
            "second_power_cycle"
        ]
        self.dead_trig = config_dict["sensor_error_program"]["dead"]

    def track(self, results: dict) -> dict:
        """Determine how many subsequent errors occur on each sensor"""
        for sensor, readings in results.items():
            if self.dead_sensors[sensor]:
                continue
            no_nones = True
            for variable, r in readings.items():
                # increment if any readings are None
                if r.value is None:
                    self.sensor_errors[sensor] += 1
                    logger.error(
                        "Error detected on '%s': reading was '%s' with '%s %s'",
                        sensor,
                        variable,
                        r.value,
                        r.unit,
                    )
                    no_nones = False
                    break
            # reset error counter if no errors
            if no_nones:
                self.sensor_errors[sensor] = 0

        first_i2c_cycles = self._dictonary_subset(
            self.sensor_errors, self.first_i2c_cycle_trig, operator.eq
        )
        second_i2c_cycles = self._dictonary_subset(
            self.sensor_errors, self.second_i2c_cycle_trig, operator.eq
        )
        first_power_cycles = self._dictonary_subset(
            self.sensor_errors, self.first_power_cycle_trig, operator.eq
        )
        second_power_cycles = self._dictonary_subset(
            self.sensor_errors, self.second_power_cycle_trig, operator.eq
        )

        if first_i2c_cycles or second_i2c_cycles:
            self.sensor_error_sol["i2c_cycle"] = True
        else:
            self.sensor_error_sol["i2c_cycle"] = False

        if first_power_cycles or second_power_cycles:
            self.sensor_error_sol["power_cycle"] = True
        else:
            self.sensor_error_sol["power_cycle"] = False

        if first_i2c_cycles:
            for s in first_i2c_cycles.keys():
                logger.info("%s caused a first instance of an i2c bus cycle", s)
        if second_i2c_cycles:
            for s in second_i2c_cycles.keys():
                logger.info("%s caused a second instance of an i2c bus cycle", s)
        if first_power_cycles:
            for s in first_power_cycles.keys():
                logger.info(
                    "%s caused a first instance of a sensor suite power cycle (if available)",
                    s,
                )
        if second_power_cycles:
            for s in second_power_cycles.keys():
                logger.info(
                    "%s caused a second instance of a sensor suite power cycle (if available)",
                    s,
                )

        declare_dead_sensors = [
            s for s, ec in self.sensor_errors.items() if ec == self.dead_trig
        ]

        if declare_dead_sensors:
            for s in declare_dead_sensors:
                self.sensor_errors[s] = 0
                self.dead_sensors[s] = True
                logger.critical(
                    "%s declared dead. No further recovery measures for %s", s, s
                )

        return self.sensor_error_sol

    def _dictonary_subset(
        self, d: dict, x: float, op_func: Callable[[float, float], bool]
    ) -> dict:
        """Find the subset of a dictonary where the elements of the
        subset have values of op_func related to to x.
        (i.e. all key-values pairs where x is "greater than" x=3)
        Note that op_func is one of the operators from the operator module"""
        subset_D = {k: v for k, v in d.items() if op_func(v, x)}
        return subset_D
