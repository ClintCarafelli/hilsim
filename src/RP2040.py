import os
import logging
import serial
import time
from datetime import datetime, timedelta
from random import random
from pathlib import Path
from src.LoadTOML import LoadTOML


logger = logging.getLogger(__name__)


class RP2040Communication():
    def __init__(self, config_dict: dict, **kwargs) -> None: 
        super().__init__(config_dict=config_dict, **kwargs) 
        self.config: dict           = config_dict
        self.sim: bool              = config_dict["RP_connection"]["sim"]
        self.super_sim: bool        = config_dict["RP_connection"]["super_sim"]
        self.baud_rate: int         = int(config_dict["RP_connection"]["baud_rate"])
        self.device_ID: str         = config_dict["RP_connection"]["device_ID"]
        self.fake_device_ID: str    = config_dict["RP_connection"]["device_ID"]
        self.time_out: float        = float(config_dict["RP_connection"]["time_out"])
        self.read_time: float       = float(config_dict["RP_connection"]["read_time"])
        self.hb_send_msg: str       = config_dict["RP_connection"]["hb_send_msg"] 
        self.hb_recieve_msg: str    = config_dict["RP_connection"]["hb_receive_msg"] 

    def _initialize_connection(self) -> None:
        """create the serial connection"""
        logger.info("Initalizing RP2040 serial connection")
        if not self.super_sim:
            if self.sim: 
                device_name = self.fake_device_ID
            else: 
                device_name = self.device_ID

            try:
                self.ser = serial.Serial(device_name, self.baud_rate, self.time_out)
            except Exception as e: 
                logger.error(f"Error initializing serial connection to RP2040: {e}")
        else:
            self.ser = FakeSerial(self.config)
    def _disconnect(self) -> None:
        try:
            logger.info("Closing the serial port to the RP2040")
            self.ser.close()
            logger.info("Successfully closed the connection to the RP2040")
        except Exception as e: 
            logger.error(f"Could not close serial port: {e}")

    def _read_and_write(self, send_msg: str, recieve_msg: str) -> bool:

        try: 
            received_data = []
            logger.info(f"sending message '{send_msg}' to RP2040")
            self.ser.write(send_msg.encode())
            current_time = datetime.now()
            confirmed = False
            while datetime.now() - current_time < timedelta(seconds=self.read_time):
                line = self.ser.readline().decode().strip()
                received_data.append(line)
                if recieve_msg in line: 
                    logger.info(f"received correct confirmation: '{line}'")
                    confirmed = True
                    return True

            if not confirmed:
                received_data_str = ""
                for e in received_data:
                    received_data_str  = " ".join(received_data)
                
                logger.error(f"Command '{send_msg}' sent to RP2040 but no/incorrect " + 
                             f"confirmation: '{received_data_str}'")
                return False 

        except Exception as e: 
            msg = f"Error writing to RP2040: {e}"
            logger.error(msg)
            return False

class RP2040AdvancedErrorHandling():
    def __init__(self, config_dict: dict, **kwargs) -> None: 
        super().__init__(**kwargs) 
        self.config            = config_dict
        self.retries           = int(config_dict["RP_connection"]["retries"])
        self.connection_cycles = int(config_dict["RP_connection"]["connection_cycles"])
        self.power_cycles      = int(config_dict["RP_connection"]["power_cycles"])

    def advanced_connection(self, send_msg: str,receive_msg: str, pca: bool) -> dict:
        
        recovery_location = {"retries": False, 
                             "software_cycle": False,
                             "power_cycle": False}
        confirmed = self._retries(send_msg, receive_msg)
        if confirmed:
            recovery_location["retries"] = True
            return recovery_location
        else:
            confirmed = self._reconnect()

        if confirmed:
            recovery_location["software_cycle"] = True
            return recovery_location
        else: 
            confirmed = self._power_cycle(pca)

        if confirmed:
            recovery_location["power_cycle"] = True
            return recovery_location
        else: 
            return recovery_location

    def _retries(self, send_msg: str, recieve_msg: str) -> bool:
        """ retry sending the message to determine if """

        for i in range(self.retries):
            logger.info(f"attempting retry {str(i+1)}")
            confirmed = self._read_and_write(send_msg, recieve_msg)
            if confirmed:
                logger.info(f"Received response on retry {str(i+1)}," \
                             "RP2040 connection re-established.")
                return True 
            
        logger.info("Max retries hit")
        return False
    
    def _reconnect(self) -> bool:
        for i in range(self.connection_cycles):
            logger.info(f"attempting software reconnection, attempt {str(i+1)}")
            self._disconnect()
            self._initialize_connection()
            confirmed = self._read_and_write("ping", "pong")
            if confirmed:
                logger.info("Connection re-established via software cycling on " \
                f"attempt {str(i+1)}, heartbeat received.")
                return True
            
        logger.info("Max connection cycles hit")
        return False

    def _power_cycle(self, pca: bool) -> bool:
        if pca: 
            logger.info("Power cycling available")
            for i in range(self.power_cycles):
                try: 
                    logger.info(f"Power cycling USB hub, attempt {str(i+1)}")
                    # input bash script here
                    confirmed = self._read_and_write("ping", "pong")
                    if confirmed: 
                        logger.info("Connection re-established via power cycling" \
                        f" on attempt {str(i+1)}, heartbeat received")
                        return True
                except Exception as e: 
                    logger.error(f"failed to perfrom USB power cycle: {e}")
            logger.info("Max power cycles hit")
            return False 
        else: 
            logger.info("power cycling unavailable.")
            return False
        

class Controls(RP2040Communication, RP2040AdvancedErrorHandling):
    def __init__(self, config_dict: dict, **kwargs) -> None:
        self.config_dict = config_dict
        super().__init__(config_dict=config_dict, **kwargs)

    def connect(self):
        self._initialize_connection()

    def full_communcation_handling(self, pca, 
                                   send_msg:str|None=None, 
                                   receive_msg:str|None=None) -> bool | str:
        """Apply full communication protocol to RP2040 using basic read/writes and
          advanced error handling techniques"""
        logger.info("Sending heartbeat to RP2040")

        if send_msg == None: 
            send_msg = self.hb_send_msg

        if receive_msg == None: 
            receive_msg = self.hb_recieve_msg


        confirmed = self._read_and_write(send_msg, receive_msg)

        if not confirmed: 
            logger.info("Moving to advanced error handling on RP2040-host communication")
            recovery_location = self.advanced_connection(send_msg, receive_msg, pca)

            if recovery_location["retries"]: 
                logger.info("Message successfully sent and confirmed on retries")
            elif recovery_location["software_cycle"]:
                logger.info("RP2040 connection recovered with software cycle, resending message:")
                new_confirmed = self._read_and_write(send_msg, receive_msg)
            elif recovery_location["power_cycle"]:
                logger.info("RP2040 connection recovered with power cycle, resending message:")
                new_confirmed = self._read_and_write(send_msg, receive_msg)
            else: 
                logger.info("Unable to reestablish confirmed communcation with RP2040. Moving on "
                "with no further recovery until new trigger.")
                return False
            if not new_confirmed:
                logger.info("Failure to send message and confirm message to RP2040 after " \
                    "re-establishing connection. Moving on with no further retries until " \
                    "new trigger. ")
                return False 
        return True 
    
    def heart_beat(self, send_msg:str|None=None, receive_msg:str|None=None) -> bool:
        """send heart beat request to RP2040"""
        logger.info("Sending heartbeat to RP2040")

        if send_msg is None: 
            send_msg = self.hb_send_msg

        if receive_msg is None: 
            receive_msg = self.hb_recieve_msg

        confirmation: bool = self.full_communcation_handling(send_msg, receive_msg)

        return confirmation
    
    def GPIO(self, pca: bool, channel: int, side: int, time: int) -> bool:
        """ Send CO2 injection message"""
        msg = "GPIO, " + str(channel) + ", " + str(side) + ", " + str(time)
        confirmation = self.full_communcation_handling(msg, msg)
        return confirmation

    def PWM(self, pca: bool, channel: int, clicks: int, time: int) -> bool:
        """ Send CO2 injection message"""
        msg = "PWM, " + str(channel) + ", " + str(clicks) + ", "  + str(time)
        confirmation = self.full_communcation_handling(msg, msg)
        return confirmation
    
    def Lights(self, pca: bool, channel: int, g: int, r: int, b: int, w) -> bool:
        """ Send CO2 injection message"""
        msg = "Lights, " + str(g) + ", " + str(r) + ", "  + str(b) + ", " + str(w)
        confirmation = self.full_communcation_handling(msg, msg)
        return confirmation

    
class FakeSerial():
    def __init__(self, config: dict) -> None:
        self.failure_rate   = config["RP_connection"]["super_sim_fr"]
        self.read_time      = config["RP_connection"]["read_time"]
        self.hb_send_msg    = config["RP_connection"]["hb_send_msg"]
        self.hb_receive_msg = config["RP_connection"]["hb_receive_msg"]
        self.msg            = ""

    def write(self, msg: bytes):
        self.msg = msg
        return None
    
    def readline(self):
        # multiplied by 0.7 to help deal with timing uncertainty in non-RTOS
        confirm_wait = random() * self.read_time * 0.7
        start_time = datetime.now() 
        if random() < self.failure_rate:
            # Don't respond right away as if you do this leads to a huge concatenation issue for
            # an error string and takes forever. 
            time.sleep(self.read_time * 0.25)
            return "".encode()
        else: 
            if self.hb_send_msg.encode() in self.msg: 
                self.return_msg = self.hb_receive_msg.encode()
            
            else: 
                self.return_msg = self.msg
            while True:
                current_td = datetime.now() - start_time
                if current_td >= timedelta(seconds=confirm_wait):
                    return self.return_msg
    def close(self):
        """ fake closing the serial port—doesn't actually do anything in sim"""
        pass
                
if __name__ == "__main__":

    # Get controls configuration from the controls_config.toml
    controls_config_path = Path(__file__).parent.parent / "controls_config.toml"
    controls_config = LoadTOML(controls_config_path)
    controls_config["main_path"] = os.path.dirname(os.path.abspath(__file__))

    # Create logger 
    new_logger_name = "test_log.txt"
    current_log_handler = logging.basicConfig(filename=new_logger_name,
	level=logging.DEBUG, 
	format='%(asctime)s - %(levelname)s - %(message)s')

    # Check CDH controller functionality
    CDH_controller = Controls(controls_config)
    CDH_controller.connect()
    CDH_controller.heart_beat()
    CDH_controller.GPIO(True, 8, 1, 50)
    CDH_controller.PWM(True, 8, 2300, 1000)
    CDH_controller.Lights(True, 8, 40, 40, 40, 40)
        



