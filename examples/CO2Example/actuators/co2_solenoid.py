from hilsim.core.actuators import ActuatorBase

class CO2Solenoid(ActuatorBase):
    """Solenoid driver to create commands and update world state"""

    def build_command(self, target_state: str) -> str:
        """Create command to be sent to the microcontroller"""
        pin = str(self.settings["pin"])
        if target_state == "open":
            package = pin + "," +  str(1)
        else:
            package = pin + "," +  str(0)
        return package

    def effect_CO2(self) -> float:
        """Define the physical effects of the CO2 solenoid on CO2"""
        if self.hardware_state == "open":
            return 1000 * self.dt
        else:
            return 0

    def effect_current(self) -> float:
        """Define the physical effects of the CO2 solenoid on the system current"""
        if self.hardware_state == "open":
            return 1001.6
        else:
            return 0
