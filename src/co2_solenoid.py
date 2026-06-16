
from src.actuators import ActuatorBase, WorldState
from src.controls import Controls

class CO2Solenoid(ActuatorBase): 
    """Solenoid driver to create commands and update world state"""
    def __init__(self, config: dict, world_state: WorldState, controller: Controls) -> None: 
        super().__init__(config, world_state, controller)

    def build_command(self, target_state: str) -> bool: 
        """Create command for microcontroller and send command and send it"""
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
        
    def effect_system_current(self) -> float: 
        """Define the physical effects of the CO2 solenoid on system current"""
        if self.hardware_state == "open":
            return 1001.6
        else: 
            return 0 
