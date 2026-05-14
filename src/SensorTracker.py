import logging 
import operator

logger = logging.getLogger(__name__)

class SensorTracker():
    def __init__(self, config_dict: dict) -> None: 
        enabled_sensors = config_dict["sensor_params"].get("enabled_sensors", [])

        self.dead_sensors: dict[str, bool]     = dict.fromkeys(enabled_sensors, False)
        self.sensor_errors: dict[str, bool]    = dict.fromkeys(enabled_sensors, 0)
        self.sensor_error_sol: dict[str, bool] = {"i2c_cycle": False, "power_cycle_ss": False}

        self.first_i2c_cycle_trig    = config_dict["sensor_error_program"]["first_i2c_cycle"]
        self.second_i2c_cycle_trig   = config_dict["sensor_error_program"]["second_i2c_cycle"]
        self.first_power_cycle_trig  = config_dict["sensor_error_program"]["first_power_cycle"]
        self.second_power_cycle_trig = config_dict["sensor_error_program"]["second_power_cycle"]
        self.dead_trig               = config_dict["sensor_error_program"]["dead"]

    def track(self, results: dict) -> dict:
        """ Determine how many subsequent errors occur on each sensor"""
        for sensor, readings in results.items():
            if self.dead_sensors[sensor]: 
                continue
            no_Nones = True
            for r in readings:
                # increment if any are None
                if r.value is None: 
                    self.sensor_errors[sensor] += 1
                    logging.info(f"Error detected on {sensor}, reading was {r.name} with {r.value} {r.unit}")
                    no_Nones = False
                    break
            # reset error counter if no errors
            if no_Nones:
                self.sensor_errors[sensor] = 0

        first_i2c_cycles    = self._dictonary_subset(self.sensor_errors, self.first_i2c_cycle_trig, operator.eq)
        second_i2c_cycles   = self._dictonary_subset(self.sensor_errors, self.second_i2c_cycle_trig, operator.eq)
        first_power_cycles  = self._dictonary_subset(self.sensor_errors, self.first_power_cycle_trig, operator.eq)
        second_power_cycles = self._dictonary_subset(self.sensor_errors, self.second_power_cycle_trig, operator.eq)

        if first_i2c_cycles or second_i2c_cycles:
            self.sensor_error_sol["i2c_cycle"] = True
        else:
             self.sensor_error_sol["i2c_cycle"] = False

        if first_power_cycles or second_power_cycles:
            self.sensor_error_sol["power_cycle_ss"] = True
        else: 
             self.sensor_error_sol["power_cycle_ss"] = False

        if first_i2c_cycles:
            for s in first_i2c_cycles.keys():
                logger.info(f"{s} caused a first instance of an i2c bus cycle")
        if second_i2c_cycles:
            for s in second_i2c_cycles.keys():
                logger.info(f"{s} caused a second instance of an i2c bus cycle")
        if first_power_cycles:
            for s in first_power_cycles.keys():
                logger.info(f"{s} caused a first instance of a sensor suite power cycle (if available)")
        if second_power_cycles:
            for s in second_power_cycles.keys():
                logger.info(f"{s} caused a second instance of a sensor suite power cycle (if available)")

        declare_dead_sensors = [s for s, ec in self.sensor_errors.items() if ec == 7]

        if declare_dead_sensors:
            print("declaring dead sensors")
            for s in declare_dead_sensors:
                self.sensor_errors[s] = 0
                self.dead_sensors[s] = True
                logger.info(f"{s} decared dead. No further recovery measures for {s}")

        return self.sensor_error_sol
    
    def _dictonary_subset(self, D: dict, x: float, op_func: any) -> dict:
        """ Find the subset of a dictonary where the elements of the 
             subset have values of op_func related to to x. 
             (i.e. all key-values pairs where x is "greater than" x=3)
             Note that op_func is one of the operators from the operator module"""
        subset_D = {k:v for k,v in D.items() if op_func(v, x)}
        return subset_D
    