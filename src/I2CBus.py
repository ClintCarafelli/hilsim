from I2CExceptions import I2CInitError, I2CDeInitError
import logging

logger = logging.getLogger(__name__)

class I2CBus: 
    def __init__(self, sim_all: bool) -> None: 
        self.sim_all = sim_all
        self.initalized_i2c = False


    def initialize_i2c_bus(self) -> any:
        if self.sim_all: 
            logger.info("Initalizing I2C Bus")
            self.initalized_i2c = True
            return None
        else:
            try: 
                logger.info("Importing board and busio modules required for I2C")
                import board
                import busio
                logger.info("Initalizing I2C bus")
                i2c = busio.I2C(board.SCL, board.SDA)
                self.initalized_i2c = True
                logger.info("Successfully initalized I2C bus")
                return i2c
            except: 
                 msg = "Unable to initialize the I2C bus. Both the board and " \
                 "busio libraries are required, which follow from the installation of the adafruit_blinka" \
                 "library, Check if these are installed"
                 logger.error(msg)
                 raise I2CInitError(msg)
            
    def deinitialize_i2c_bus(self, i2c_bus: any) -> None: 
        if not self.initalized_i2c: 
            msg = "no i2c_bus object to deinitialize"
            logger.error(msg)
            raise I2CDeInitError(msg)
        if self.sim_all:
            logger.info("Deinitialzing the I2C bus")
        else: 
            try: 
                logger.info("Deinitializing I2C bus and freeing resources")
                i2c_bus.dinit()
                self.initialize_i2c = False
                logger.info("successfully deinitialized I2C bus")
            except: 
                msg = "Unable to deinitialize the current i2c bus"
                logger.error(msg)
                raise I2CDeInitError(msg)
        




            
