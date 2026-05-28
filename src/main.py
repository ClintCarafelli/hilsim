import os 
import logging 
import time
from src.LoadTOML import LoadTOML
from src.SensorManager import SensorManager
from src.SensorTracker import SensorTracker
from src.I2CBus import I2CBus
from pathlib import Path

from src.CreateFakeSensors import CreateFakeSensors

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
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
fake_sensors = CreateFakeSensors(sensor_config)
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# Create sensor manager and sensor tracker and initalize sensors
sensor_manager = SensorManager(sensor_config, i2c_bus, fake_sensors.sensors, True)
sensor_manager.initialize_all()
sensor_tracker = SensorTracker(sensor_config)

# General parameters
pca = True    # defines if power cycling the USB ports is avaliable or not 

# Set original, known hardware states. 
status_dict = {"solenoid": "off", "servo": "off", "purple_lights": "on", "white_lights": "off"}
sensor_manager._sensors["INA260"].device.status = status_dict

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
    sensor_tracker.track(data)
    print()
    time.sleep(2)