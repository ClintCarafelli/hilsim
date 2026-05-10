class SensorError(Exception):
    """ Base for sensor-related errors"""
    def __init__(self, sensor_id: str, message: str) -> None: 
        self.sensor_id = sensor_id
        super().__init__(f"[{sensor_id}] {message}")

class SensorInitError(SensorError):
    """Raised when a sensor fails to initialize"""
 
class SensorReadError(SensorError):
    """Raised when a sensor is initialized but a read attempt fails."""

class ConfigError(SensorError):
    """Raised when the config file is missing, malformed, or incomplete."""

class SensorErrorHandler(Exception):
    def __init__(self, error_strat: str, message: str) -> None:
        self.error_strat = error_strat
        super().__init__(f"error strategy issue: [{error_strat}] {message}")

class ConfigErrorHandler(SensorErrorHandler):
    """Raised when the error_stat does not have its own config block"""