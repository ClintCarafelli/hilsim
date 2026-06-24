# hilsim
A Python package for rapid hardware-in-the-loop (HIL) and software-in-the-loop (SIL) simulation, 
designed for software/hardware testing, deployment, and development. 

## Installation
pip install hilsim

## Quick Start
See the [examples](examples/) folder for a host of configuration files, sensors, and actuators. 

## How It Works
hilsim generates a project structure where the developer has four main tasks: 
   1) fill out configuration files
   2) Writes basic drivers for sensors based on a template. 
   3) Describe the physics/behavior of actuators (anything that changes the state of the world), also based on a template.
   4) Write the main logic.

A simple run command then simulates the entire system. Switching the "sim" keyword for either a sensor, device, or actuator allows the user to rapidly switch between simulating a component and deploying the actual hardware. No need to worry about any middleware or fatal exceptions in the background.

## Features
- Data recording. 
- User defined event driven log file management with a built-in detailed message logging system. 
- Standardized serial protocol with built-in recovery.
- High-level i2c bus interactions with built-in recovery.
- Simulate latency between the host and peripheral device communication and actual hardware deployment.
- Simulate sensor errors/failures.
- Simulate noise and drift in sensors. 
- Simulate host-peripheral device communication failures. 
- Simulate hardware failures.
- Background dynamics simulation. Background dynamics run on a high-speed background thread (on the ms level) which sensors may routinely pull from, mirroring the continuous nature of system dynamics and separating them from the discrete nature of sensor reads.

## Current Limitations
Currently, the "supported" i2c_bus wraps the board and busio libraries, allowing hilsim to accommodate a wide range of readily-available/cheap sensors from manufacturers like Adafruit. A future release will include support for the smbus library, allowing the the use of custom sensors / i2c devices at a lower level. 

## Roadmap
- Support for the smbus library.
- Rapid power cycling / software cycling integration. The current release flags errors that the developer can accommodate in main, but does not have the capability to power cycle devices. 
- SPI support
- Virtual serial ports with socat, ideal for testing microcontroller code alongside the host.  
