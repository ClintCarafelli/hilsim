import os
import logging
from datetime import datetime, timedelta
import serial

logger = logging.getLogger(__name__)


class RP2040Communication():
    def __init__(self, config_dict: dict) -> None: 

        self.sim: bool           = config_dict["RP_connection"]["sim"]
        self.super_sim: bool     = config_dict["RP_connection"]["super_sim"]
        self.baud_rate: int      = int(config_dict["RP_connection"]["baud_rate"])
        self.device_ID: str      = config_dict["RP_connection"]["device_ID"]
        self.time_out: float     = float(config_dict["RP_connection"]["time_out"])
        self.read_time: float    = float(config_dict["RP_connection"]["read_time"])
        self.hb_send_msg: str    = config_dict["RP_connection"]["hb_send_msg"] 
        self.hb_recieve_msg: str = config_dict["RP_connection"]["hb_recieve_msg"] 

    def initialize_connection(self) -> None:
        """create the serial connection"""

        if self.sim:
            raise NotImplementedError("sim mode not implimented")
        
        elif self.super_sim:
            logger.info("Initalizing super fake RP2040 serial connection")
            self.ser = self.super_sim
        else: 
            try: 
                logger.info("Initalizing RP2040 serial connection")
                self.ser = serial.Serial(self.device_ID, self.baud_rate, self.time_out)
            except Exception as e:
                msg = f"failed to  initialize RP2040 connection: {e}"
                logger.error(msg)

    def _read_and_write(self, send_msg: str, recieve_msg: str) -> None:

        try: 
            logger.info(f"sending message {send_msg} to RP2040")
            self.ser(send_msg)

            current_time = datetime.now()
            confirmation_recieved: bool = False
            while datetime.now() - current_time < timedelta(seconds=self.read_time) and not confirmation_recieved:
                line = self.ser.readline()
                if recieve_msg in line: 
                    confirmation_recieved = True
                
            if not confirmation_recieved: 
                raise NotImplementedError("advanced error handling")

        except Exception as e: 
            msg = f"Error writing to RP2040: {e}"
            logging.error(msg)

    def heart_beat(self) -> None:
        raise NotImplementedError

    def PWM(self,channel:int, clicks: int) -> None:
        raise NotImplementedError
    
    def lighting(self, color_list: list[int]) -> None:
        raise NotImplementedError
    

    def super_sim(self, input_1, input_2:str | float, input_3:str | float):

        if input_1 == "PWM":
            send_str = "PWM," + str(input_2)  +", " + str(input_3)
            self.ser.write()
        elif input_1 == "lights":
            pass
        elif input_1 == "heart_beat":
            pass

        


