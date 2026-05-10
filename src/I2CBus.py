from I2CExceptions import I2CInitError, I2CDeInitError

class I2CBus: 
    def __init__(self, sim_all: bool) -> None: 
        self.sim_all = sim_all
        self.initalized_i2c = False


    def initialize_i2c_bus(self) -> None | I2C:
        if self.sim_all: 
            return None
        else:
            try: 
                import board
                import busio
                i2c = busio.I2C(board.SCL, board.SDA)
                self.initalized_i2c = True
                return i2c
            except: 
                 raise I2CInitError("Unable to initialize the i2c bus. Both the board and " \
                 "busio libraries are required, which follow from the installation of the adafruit_blinka" \
                 "library. Check if these are installed.")
            
    def deinitialize_i2c_bus(self, i2c_bus: any) -> None: 
        if not self.initalized_i2c: 
            raise I2CDeInitError("no i2c_bus to deinitialize.")
        if self.sim_all:
            pass
        else: 
            try: 
                i2c_bus.dinit()
                self.initialize_i2c = False
            except: 
                raise I2CDeInitError("Uable to deinitialize the current i2c bus.")
        




            
