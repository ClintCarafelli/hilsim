"""Holds the relevant classes for controls handling including:
- RP2040Communication
- RP2040AdvancedErrorHandling
- Controls"""

import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from random import random

import serial
from rich import print
from serial import SerialException

from src.device_exceptions import DeviceConnectionError
from src.load_toml import LoadTOML

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------------------
class FakeSerial:
    """Fake Serial class that holds the methods of serial.Serial relevant to
    the CommunicationInterface class"""

    def __init__(
        self, super_sim_fr: float | int, read_time: float, hb_sm: str, hb_rm: str
    ) -> None:
        self.failure_rate = super_sim_fr
        self.read_time = read_time
        self.hb_send_msg = hb_sm
        self.hb_receive_msg = hb_rm
        self.msg = "".encode()
        self.return_msg: bytes

    def write(self, msg: bytes) -> None:
        """Write a message (doesn't really do much in since this is fake)"""
        self.msg = msg

    def readline(self) -> bytes:
        """Return bytes and an expected response"""
        # multiplied by 0.7 to help deal with timing uncertainty in non-RTOS
        confirm_wait = random() * self.read_time * 0.7
        start_time = datetime.now()
        if random() < self.failure_rate:
            # Don't respond right away as if you do this leads to a huge 
            # concatenation issue for an error string and takes forever.
            time.sleep(self.read_time * 0.25)
            return "".encode()
        if self.hb_send_msg.encode() in self.msg:
            self.return_msg = self.hb_receive_msg.encode()
        else:
            self.return_msg = self.msg
        while True:
            current_td = datetime.now() - start_time
            if current_td >= timedelta(seconds=confirm_wait):
                return self.return_msg

    def close(self) -> None:
        """fake closing the serial port—doesn't actually do anything in sim"""


# ---------------------------------------------------------------------------------------
class CommunicationInterface(ABC):
    """Define abstract communication interface for serial connections"""

    def __init__(self, config_dict: dict, device_name: str) -> None:
        self.sim: bool = config_dict["sim"]
        self.super_sim: bool = config_dict["super_sim"]
        self.super_sim_fr: bool = config_dict["super_sim_fr"]
        self.baud_rate = int(config_dict["baud_rate"])
        self.device_id: str = config_dict["device_ID"]
        self.fake_device_id: str = config_dict["fake_device_ID"]
        self.time_out = float(config_dict["time_out"])
        self.read_time = float(config_dict["read_time"])
        self.hb_sm: str = config_dict["hb_send_msg"]
        self.hb_rm: str = config_dict["hb_receive_msg"]
        self.pca = True
        self.connected = False
        self.ser: serial.Serial | FakeSerial
        self.device_name = device_name

    @abstractmethod
    def connect(self) -> bool:
        """Enforce a connect method"""

    @abstractmethod
    def disconnect(self) -> None:
        """Enforce a disconnect method"""

    @abstractmethod
    def read_and_write(
        self,
        send_msg: str,
        receive_msg: str,
    ) -> bool:
        """Enforce a read and write method"""


# ---------------------------------------------------------------------------------------
class SerialInterface(CommunicationInterface):
    """Directly communicate with an serial interface Chip over serial connection (usb)"""

    def __init__(self, config_dict: dict, device_name: str) -> None:
        logger.info("Creating %s", device_name)
        super().__init__(config_dict, device_name)

    def connect(self) -> bool:
        """create the serial connection"""
        logger.info("Initalizing serial connection for %s", self.device_name)
        if not self.super_sim:
            if self.sim:
                device_id = self.fake_device_id
            else:
                device_id = self.device_id

            try:
                self.ser = serial.Serial(
                    port=device_id, baudrate=self.baud_rate, timeout=self.time_out
                )
                self.connected = True
                return True
            except SerialException as e:
                logger.error(
                    "Error initializing serial connection to %s: %s",
                    self.device_name,
                    str(e),
                )
                return False
        else:
            self.ser = FakeSerial(
                self.super_sim_fr, self.read_time, self.hb_sm, self.hb_rm
            )
            self.connected = True
            return True

    def disconnect(self) -> None:
        """Disconnect from the serial port"""
        try:
            logger.info("Closing the serial port to %s", self.device_name)
            self.ser.close()
            self.connected = False
            logger.info("Successfully closed the connection to %s", self.device_name)
        except SerialException as e:
            logger.error("Could not close serial port to %s: %s", self.device_name, e)

    def read_and_write(self, send_msg: str, receive_msg: str) -> bool:
        """Read and write over the serial connection"""
        try:
            received_data = []
            logger.info("sending message '%s' to %s", send_msg, self.device_name)
            self.ser.write(send_msg.encode())
            start_time = datetime.now()
            while datetime.now() - start_time < timedelta(seconds=self.read_time):
                line = self.ser.readline().decode().strip()
                received_data.append(line)
                if receive_msg in line:
                    logger.info("received correct confirmation: '%s'", line)
                    return True

            received_data_str = " ".join(received_data)

            logger.error(
                "Command '%s' sent to %s but no/incorrect confirmation: '%s'",
                send_msg,
                self.device_name,
                received_data_str,
            )
            return False

        except SerialException as e:
            msg = f"Error writing to the serial port for {self.device_name}: {e}"
            logger.error(msg)
            return False


# ---------------------------------------------------------------------------------------
class AdvancedCommunication:
    """Check and handle communication with the a device that is a communication
    interface"""

    def __init__(self, config_dict: dict, device: CommunicationInterface) -> None:
        self.retries = int(config_dict["retries"])
        self.connection_cycles = int(config_dict["connection_cycles"])
        self.power_cycles = int(config_dict["power_cycles"])
        self.hb_sm = config_dict["hb_send_msg"]
        self.hb_rm = config_dict["hb_receive_msg"]
        self.device = device
        self.device_name = device.device_name
        #self.device_name = self.device.__class__.__name__

    def __repr__(self):
        return f"Instance of AdvancedCommunication for {self.device_name}"

    def send(self, send_msg: str, receive_msg: str, secondary_send=False) -> bool:
        """Send the initial command and check for response"""
        logger.info(
            "Will send '%s' to %s, expecting '%s' in return for confirmation",
            send_msg,
            self.device_name,
            receive_msg,
        )
        result = self.device.read_and_write(send_msg, receive_msg)
        if not result and not secondary_send:
            logger.info("Continuing to connection recovery")
        if not result and secondary_send:
            logger.info(
                "connection was recovered with heartbeat, but failed on \
                a secondary send of command '%s'. No further \
                recovery for this command until called again.",
                send_msg,
            )
        return result

    def _retries(self, send_msg: str, receive_msg: str) -> bool:
        """retry sending the message to determine if error is transient"""

        for i in range(self.retries):
            logger.info("attempting retry %s", str(i + 1))
            confirmed = self.device.read_and_write(send_msg, receive_msg)
            if confirmed:
                logger.info(
                    "received correct response on retry %s, %s connection re-established.",
                    str(i + 1),
                    self.device_name,
                )
                return True

        logger.info("Max retries hit")
        return False

    def _software_cycle(self) -> bool:
        """drop and reinitialize serial connection, check with heart beat"""
        for i in range(self.connection_cycles):
            logger.info("attempting software reconnection, attempt %s", str(i + 1))
            self.device.disconnect()
            # add bash script here
            self.device.connect()
            confirmed = self.device.read_and_write(self.hb_sm, self.hb_sm)
            if confirmed:
                logger.info(
                    "Connection re-established via software cycling on "
                    "attempt %s, heartbeat received.",
                    str(i + 1),
                )
                return True

        logger.info("Max connection cycles hit")
        return False

    def _power_cycle(self) -> bool:
        """Power cycle all usb ports chip"""
        if self.device.pca:
            logger.info("power cycling available")
            for i in range(self.power_cycles):
                try:
                    logger.info("power cycling USB hub, attempt %s", str(i + 1))
                    # input bash script here
                    confirmed = self.device.read_and_write(self.hb_sm, self.hb_rm)
                    if confirmed:
                        logger.info(
                            "Connection re-established via power cycling on attempt %s, "
                            "heartbeat received",
                            str(i + 1),
                        )
                        return True
                except Exception as e:
                    logger.error("failed to perfrom power cycle: %s", e)
            logger.info("max power cycles hit, connection not recovered")
            return False

        logger.info("power cycling unavailable")
        return False

    def advanced_connection(self, send_msg: str, receive_msg: str) -> dict[str, bool]:
        """Handle errors with a heriarchy of recovery methods"""
        msg_location = {
            "confirmed": False,
            "nominal": False,
            "retries": False,
            "software_cycle": False,
            "power_cycle": False,
        }
        confirmed = self.send(send_msg, receive_msg)
        if confirmed:
            msg_location["nominal"] = True
            msg_location["confirmed"] = True
            return msg_location
        
        confirmed = self._retries(send_msg, receive_msg)
        if confirmed:
            msg_location["retries"] = True
            msg_location["confirmed"] = True
            return msg_location
        
        reconnected = self._software_cycle()
        if reconnected:
            msg_location["software_cycle"] = True
            result = self.send(send_msg, receive_msg, True)
            if result:
                msg_location["confirmed"] = True
            return msg_location
        
        reconnected = self._power_cycle()
        if reconnected:
            msg_location["power_cycle"] = True
            result = self.send(send_msg, receive_msg, True)
            if result:
                msg_location["confirmed"] = True
            return msg_location
        return msg_location


# ---------------------------------------------------------------------------------------
class Controls:
    """Perform controls for any registered device"""

    def __init__(self, device_dict: dict[str, AdvancedCommunication]) -> None:
        self.devices = device_dict

    def heart_beat(self, device_id: str, advanced_connection: bool =False) -> dict[str, bool] | bool:
        """send heart beat request to device"""
        logger.info("Sending heartbeat to %s", device_id)
        confirmation: dict[str, bool] = {}

        correct_device = self.devices[device_id]
        send_msg = correct_device.hb_sm
        receive_msg = correct_device.hb_rm

        if advanced_connection: 
            confirmation = correct_device.advanced_connection(send_msg, receive_msg)
        else: 
             confirmation["confirmed"] = correct_device.send(send_msg, receive_msg)

        return confirmation

    def gpio(
        self, device_id: str, pin: int, side: int, time: int
    ) -> dict[str, bool]:
        """Send GPIO message"""
        msg = "GPIO, " + str(pin) + ", " + str(side) + ", " + str(time)
        correct_device = self.devices[device_id]
        confirmation = correct_device.advanced_connection(msg, msg)
        return confirmation

    def pwm(
        self,
        device_name: str,
        channel: int,
        duty_cycle: float,
        frequency: int,
        time: int,
    ) -> dict[str, bool]:
        """Send PWM  message"""
        msg = (
            "PWM, "
            + str(channel)
            + ", "
            + str(duty_cycle)
            + ", "
            + str(frequency)
            + ", "
            + str(time)
        )
        correct_device = self.devices[device_name]
        confirmation = correct_device.advanced_connection(msg, msg)
        return confirmation

    def lights_4ch(
        self, device_name: str, channel: int, g: int, r: int, b: int, w
    ) -> dict[str, bool]:
        """Send CO2 injection message"""
        msg = (
            "Lights, "
            + str(channel)
            + ", "
            + str(g)
            + ", "
            + str(r)
            + ", "
            + str(b)
            + ", "
            + str(w)
        )
        correct_device = self.devices[device_name]
        confirmation = correct_device.advanced_connection(msg, msg)
        return confirmation
    
    def advanced_send(self, device_name: str,  package: str) -> dict[str, bool] | bool:
        """Send a message over serial using the advanced communication heirarchy / built in error recovery""" 
        correct_device = self.devices[device_name]
        confirmation = correct_device.advanced_connection(package, package)
        return confirmation
    
    def send(self, device_name: str, package: str) -> bool: 
         """Send a message over serial with a single send, no built-in error recovery"""
         correct_device = self.devices[device_name]
         confirmation = correct_device.send(package, package)
         return confirmation 


# ---------------------------------------------------------------------------------------
def build_peripherial_devices(dc: dict) -> dict:
    """Build peripherial devices and open serial connections to them"""
    device_configs = dc["devices"]
    advanced_comms_config = dc["advanced_communication"]
    logger.info("building peripherial microcontrollers")

    device_dict = {}
    for device in dc["enabled_devices"]:
        sub_config = device_configs[device]
        device_comms = SerialInterface(sub_config, device)
        device_w_advanced_comms = AdvancedCommunication(
            advanced_comms_config, device_comms
        )
        connected = device_w_advanced_comms.device.connect()
        if not connected:
            logger.error("Error connecting to %s", device)
            raise DeviceConnectionError(
                device, "Failed to connect to device. See message logs."
            )
        logger.info("successfully connected to %s", device)
        device_dict[device] = device_w_advanced_comms
    return device_dict


# ---------------------------------------------------------------------------------------

if __name__ == "__main__":

    # Get controls configuration from the controls_config.toml
    controls_config_path = Path(__file__).parent.parent / "device_config.toml"
    controls_config = LoadTOML(controls_config_path)
    controls_config["main_path"] = os.path.dirname(os.path.abspath(__file__))

    device_map = build_peripherial_devices(controls_config)

    # Create logger
    LOGGER_NAME = "controls_log.log"
    logging.basicConfig(
        filename=LOGGER_NAME,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    print(f"[green]Output piped to {LOGGER_NAME}[/green]")

    # Check controls functionality
    CDH_controller = Controls(device_map)
    CDH_controller.heart_beat("RP2040_1")
    CDH_controller.gpio("RP2040_1", 8, 1, 50)
    CDH_controller.pwm("RP2040_2", 8, 15.5, 100000, 1000)
    CDH_controller.lights_4ch("RP2040_2", 8, 40, 40, 40, 40)
# ---------------------------------------------------------------------------------------
