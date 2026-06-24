"""Define a world state class that serves as truth for all system variables"""

import inspect
import logging
from random import gauss, random, uniform
from typing import Any

from hilsim.core.controls import Controls
from hilsim.core.world_state import WorldState

logger = logging.getLogger(__name__)
#---------------------------------------------------------------------------------------
class ActuatorBase:
    """Actuator Base Class to enforce actuator class standards"""

    registry: dict[str, Any] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        ActuatorBase.registry[cls.__name__] = cls

    def __init__(
        self, actuator_config: dict, world_state: WorldState, controller: Controls
    ) -> None:
        self.dt: float = 0.0
        self.cst: float  = 0.0
        self.time = world_state.state["time"]
        self.world_state = world_state
        self.failure_sim = actuator_config["failure_sim"]
        self.settings = actuator_config["settings"]
        self.effects = actuator_config["effects"]
        self.sim = actuator_config["settings"]["sim"]
        self.commanded_state = actuator_config["settings"]["initial_state"]
        self.hardware_state = actuator_config["settings"]["initial_state"]
        self.name = actuator_config["settings"]["name"]
        self._stuck_counter: int = 0
        self._transition_state: str = "settled"
        self._stuck: bool = False
        self._latency_remaining: float = 0.0
        self._discover_effects()
        self._controller = controller

    def send_command(self, target_state: str, advanced_connection: bool = True) -> dict[str,bool]:
        """Send command to microcontroller for target_state"""
        device_name = self.settings["device"]
        logger.info("Command triggered for %s, sending command to %s", self.name, device_name)
        logger.info("Command has target_state: %s", target_state)
        package = self.build_command(target_state)
        if advanced_connection:
            confirmation = self._controller.advanced_send(device_name, package)
        else:
            confirmation = self._controller.send(device_name, package)

        self._update_commanded_state(confirmation, target_state)
        return confirmation

    def _update_commanded_state(self, confirmation: dict[str, bool], commanded_state: str) -> None:
        """Update the commanded state attribute"""
        if confirmation["confirmed"]:
            self.commanded_state = commanded_state
            self._transition_state = "commanded"

    def _resolve_state_transition(self) -> None:
        """Determine latency and encode failure mode of hardware (i.e. actuator is stuck)"""
        if self._stuck and self._stuck_counter == 0:
            self._stuck_counter += 1 
            logger.critical("%s is stuck in state %s.", self.name, self.hardware_state)

        if not self._stuck:
            self._stuck_counter = 0

        if self._transition_state == "settled":
            return

        if self._transition_state == "commanded":
            self._latency_remaining = self._sample_latency()
            self._stuck = self._sample_stuck()
            self._transition_state = "pending_latency"

        if self._transition_state == "pending_latency":
            self._latency_remaining -= self.dt
            if self._latency_remaining <= 0:
                if self._stuck:
                    self._transition_state = "stuck"
                    logger.critical("%s is stuck", self.name)
                else:
                    self._transition_state = "settled"
                    self.hardware_state = self.commanded_state
                    self.cst = 0

    def _sample_latency(self) -> float:
        """Sample latency in milliseconds
        Note, all values divided by 1000 to convert millesconds to seconds to
        reflect the standard of self._dt"""

        dist_type = self.failure_sim["cta_latency"]["distribution"]
        if dist_type == "normal":
            mean_val = self.failure_sim["cta_latency"]["mean"] / 1000
            std_val = self.failure_sim["cta_latency"]["std"] / 1000
            return max(0, gauss(mean_val, std_val))

        if dist_type == "uniform":
            max_lat = self.failure_sim["cta_latency"]["max"] / 1000
            min_lat = self.failure_sim["cta_latency"]["min"] / 1000
            return uniform(min_lat, max_lat)

        # Could raise an error here sense dist_type would be unknown
        # sorta a silent failure right now
        logger.warning("Unknown distribution type: %s. Setting latency to zero", dist_type)
        return 0

    def _sample_stuck(self) -> bool:
        "Determine if in this sim case the actuator gets stuck in its current state"
        if random() <= self.failure_sim["stuck_probability"]:
            return True
        return False

    def update(self, dt: float) -> None:
        """Update world state based on commands, actuator latency, and effects"""
        self.cst += dt
        self.dt = dt
        if self.sim:
            self._resolve_state_transition()
            self._apply_effects()

    def _discover_effects(self):
        """Find developer effects"""
        self._effect_methods = {
            name.replace("effect_", ""): method
            for name, method in inspect.getmembers(self, predicate=inspect.ismethod)
            if name.startswith("effect_")
        }

    def _apply_effects(self) -> None:
        """Apply developer defined effects"""
        for variable_name, method in self._effect_methods.items():
            magnitude = method()
            memory_type = self._get_memory_type(variable_name)

            if "p" in memory_type:
                self.world_state.apply_delta(variable_name, magnitude)
            else:
                self.world_state.add_contributions(variable_name, self.name, magnitude)

    def _get_memory_type(self, variable_name: str) -> str:
        """Get the memory type of an actuator-effected variable"""
        return self.effects[variable_name]["effect_types"]

#---------------------------------------------------------------------------------------

