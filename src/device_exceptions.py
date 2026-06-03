class DeviceError(Exception):
    """ Base for device-related errors"""
    def __init__(self, sensor_id: str, message: str) -> None: 
        self.sensor_id = sensor_id
        super().__init__(f"[{sensor_id}] {message}")

class DeviceConnectionError(DeviceError):
    """Raised when a device fails to connect"""