# PyQTGraph_Real_Time_Plotter
A PySerial real time plotter based on PyQTGraph, PyQt6 and Pyside6 to visualise data from a PPG Sensor like MAX30102

Based on: 
- https://www.pyqtgraph.org
- https://pyqtgraph.readthedocs.io/en/latest/how_to_use.html

## Usage
You need to have an Arduino or ESP32 module connected via USB, which 

You can use the Sparkfun MAX30102 Library which you can find under:
https://github.com/sparkfun/SparkFun_MAX3010x_Sensor_Library

However, the realtime plotter expects the data to be formatted
as 'millis','red','ir'.

### Other data sources

If you want to use the real time plotter on other sensors as well
you have to adjust the "__read_data" and "update" methods.
A future update will be more generalized.

## Python Toolchain
- Create virtual enviroment in project directory
- Install requirements.txt 
```
  python3 -m venv .venv .
  . /.venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt 
```

## Run 
```
  python real_time_plotter.py
```
