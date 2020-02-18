Enjaksakavella
==============

This is a project to control an electric wheelchair with custom controllers.

Project parts:
- Electronics connecting to wheelchair
- BLE-enabled Arduino driving the electronics
- Computer with software which handles:
  - BLE connection to Arduino
  - Connection to controller
  - Visualizing controller working principles
  - Visualizing commands sent to wheelchair
- Custom controller(s)
  - Cap with eye-tracking camera

Requirements
------------

Python packages:
PySide2
OpenCV2
numpy
bluepy

Arduino libraries:
ArduinoBLE

Documentation
-------------

Documentation of the system is found in /doc folder