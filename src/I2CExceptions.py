class I2CError(Exception):
    """ Base for i2c bus related errors"""
    def __init__(self, message: str) -> None: 
        super().__init__(f"[i2c bus] {message}")

class I2CInitError(I2CError):
      """Raised when i2c bus cannot be initialized"""

class I2CDeInitError(I2CError):
      """Raised when when issue deinitalizing i2c bus"""