from hilsim.core.actuators import ActuatorBase

class Plants(ActuatorBase):

    def build_command(self, target_state: str) -> str:
        """Create command to be sent to the microcontroller"""
        # Add code here to create a package (str) that a microcontroller
        # can interpret and return it: 
        return None

    def effect_CO2(self) -> float:
        """sample effect method 1"""
        if self.hardware_state == "alive":
            return self.dt * - 5
    
