"""Handle the i2c bus"""
from hilsim.core.i2c_exceptions import I2CInitError, I2CDeInitError
import logging
from typing import Any

logger = logging.getLogger(__name__)

class I2CBus: 
    """Methods that interact with the i2c bus"""
    def __init__(self, sim_all: bool) -> None: 
        self.sim_all = sim_all
        self.initialized = False

    def initialize_i2c_bus(self) -> Any:
        """Initialize the i2c bus"""
        if self.sim_all: 
            logger.info("Initalizing I2C Bus")
            self.initialized = True
            return None
        else:
            try: 
                logger.info("Importing board and busio modules required for I2C")
                import board
                import busio
                logger.info("Initalizing I2C bus")
                i2c = busio.I2C(board.SCL, board.SDA)
                self.initialized = True
                logger.info("Successfully initalized I2C bus")
                return i2c
            except Exception as e: 
                 msg = "Unable to initialize the I2C bus. Both the board and " \
                 "busio libraries are required, which follow from the installation of " \
                 "the adafruit_blink library, Check if these are installed:" + str(e)
                 logger.error(msg)
                 raise I2CInitError(msg)
            
    def deinitialize_i2c_bus(self, i2c_bus: any) -> None: 
        """Deinitialize the i2c bus"""
        if not self.initialized: 
            msg = "no i2c_bus object to deinitialize"
            logger.error(msg)
            raise I2CDeInitError(msg)
        if self.sim_all:
            logger.info("Deinitializing the I2C bus")
        else: 
            try: 
                logger.info("Deinitializing I2C bus and freeing resources")
                i2c_bus.dinit()
                self.initialized = False
                logger.info("successfully deinitialized I2C bus")
            except Exception as e: 

                msg = "Unable to deinitialize the current i2c bus"
                logger.error(msg +":" + str(e))
                raise I2CDeInitError(msg)
        




            
