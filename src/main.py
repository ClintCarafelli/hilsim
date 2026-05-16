import os 
import logging 
import time
from LoadTOML import LoadTOML
from SensorManager import SensorManager
from SensorTracker import SensorTracker
from I2CBus import I2CBus
from pathlib import Path

# Create sensor config dict 
sensor_config_path = Path(__file__).parent.parent / "sensor_config.toml"
sensor_config = LoadTOML(sensor_config_path)
sensor_config["main_path"] = os.path.dirname(os.path.abspath(__file__))

# Create logger 
new_logger_name = "test_log.txt"
current_log_handler = logging.basicConfig(filename=new_logger_name,
	level=logging.DEBUG, 
	format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize I2C Bus
sim_all_sensors = sensor_config["sensor_params"]["sim_all"]
I2C_Handler = I2CBus(sim_all_sensors)
i2c_bus = I2C_Handler.initialize_i2c_bus()

# Create sensor manager and sensor tracker and initalize sensors
sensor_manager = SensorManager(sensor_config, i2c_bus, True)
sensor_manager.initialize_all()
sensor_tracker = SensorTracker(sensor_config)

# General parameters
pca = True    # defines if power cycling the USB ports is avaliable or not 

while True:
    print("-"*30 + "Readings" + "-"*30)
    data = sensor_manager.read_all()

    for sensor_id, readings in data.items():
        print(f"[{sensor_id}]")
        if readings:
            for r in readings: 
                print(f"    {r.name} {r.value} {r.unit}")
        else: 
            print("NO DATA")

    error_tracking = sensor_tracker.track(data)
    print(error_tracking)

    if error_tracking["i2c_cycle"]: 
        I2C_Handler.deinitialize_i2c_bus(i2c_bus)
        I2C_Handler.initialize_i2c_bus()
        sensor_manager = SensorManager(sensor_config, i2c_bus, True)
        sensor_manager.initialize_all()

    if error_tracking["power_cycle_ss"]:
        pass
        # INSERT BASH SCRIPT HERE

    print()
    time.sleep(2)