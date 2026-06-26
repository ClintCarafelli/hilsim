"""World State module"""
import threading

class WorldState:
    """Hold and update all system variables"""

    def __init__(self, config):
        self.config = config
        self._lock = threading.Lock()
        self._memory = {
            name: var["initial"] for name, var in config["variables"].items()
        }
        self.state = {name: 0 for name in config["variables"].keys()}
        self.state["time"] = 0
        self._contributions = {name: {} for name in config["variables"].keys()}
        self.update_state()  # Called to get initial conditions into state attribute

    def apply_delta(self, variable: str, delta: float) -> None:
        """Apply a change to the state variables with persistent effect"""
        with self._lock:
            if variable not in self.state:
                print(f"Incorrect suffix on effect_ method. '{variable}' is not a known world_state variable.")
                raise KeyError(f"Unknown world state variable: '{variable}'")
            self._memory[variable] += delta

    def add_contributions(self, variable: str, name: str, contribution: float) -> None:
        """Get transient contributions to state variables"""
        with self._lock:
            if variable not in self.state:
                print(f"Incorrect suffix on effect_ method. '{variable}' is not a known world_state variable.")
                raise KeyError(f"Unknown world state variable: '{variable}'")

            self._contributions[variable][name] = contribution

    def update_state(self):
        """Call this to update entire state based on actuator input"""
        with self._lock:
            for variable in self.config["variables"].keys():
                self.state[variable] = self._memory[variable] + sum(
                    [c for c in self._contributions[variable].values()]
                )

    def get(self, variable: str) -> float:
        """Get a specific variable from the state"""
        with self._lock:
            return self.state[variable]
