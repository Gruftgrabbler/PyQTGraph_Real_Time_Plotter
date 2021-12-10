import sys
import os
import csv
import numpy as np
import time

import serial.tools.list_ports
import platform

# The imports below are super critical
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg


# TODO Can the plotter be implemented in a way so that the number of graphs can be given as program parameter
#  and for example the name? So we can call the code with something like:
#  python real_time_plotter.py -n 2 red, ir
#  That would be amazing!


class PortScanner:
    @staticmethod
    def scan():
        """
        Query through all Serial ports and try to find a matching Arduino or ESP32 device
        Works on both Windows and macOS
        NOTE: It doesnt connect to the port, it's just return the ports address
        :return: the port of the connected device
        """
        print('Query serial ports in order to find an Arduino or ESP32.')
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            # MAC OS
            if platform.system() == "Darwin":
                if "CP2104" in port.description:
                    print("ESP 32 Detected at {}.".format(port.device))
                    return port.device

            # WINDOWS
            if platform.system() == "Windows":
                # TODO Implement Windows Auto Connect
                pass

        print('No Serial device found!')
        sys.exit()


class CSVWriter:
    def __init__(self, directory: str, file_path):
        """
        Create a new csv file if given file name does not exist and initialize the header row.
        :param directory: path to the directory
        :param file_path:  file name
        """

        self.file = file_path
        # CREATE TARGET DIRECTORY IF NECESSARY

        # TODO Refactor
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, 'w', newline='') as outfile:
            header = ['Millis', 'Red', 'IR']

            csv_writer = csv.DictWriter(outfile, fieldnames=header)
            csv_writer.writeheader()

        print('File created: ' + file_path)
        outfile.close()

    def write_row(self, data: list):
        """
        Write all elements of the list to the csv row
        :param data:
        :return:
        """
        with open(self.file, 'a', newline='') as outfile:
            csv_writer = csv.writer(outfile)
            csv_writer.writerow(data)


class SerialConnection:
    """
    Class which holds the Serial Connection and provides a read_data function which reads the data from the mcu
    """

    def __init__(self):
        pass

    def read_data(self):
        millis, red, ir, sample = 0
        return millis, red, ir, sample


class RealTimePlotter:
    def __init__(self, app, serial_conn: serial.Serial, csv_writer: CSVWriter, chunk_size: int = 100, max_chunks=20):
        """
        TODO Write Annotation
        :param serial_conn: Instance of the (PySerial) Serial Connection
        :param chunk_size:
        :param max_chunks:
        """

        # Serial Connection
        self.ser = serial_conn

        # CSV Writer instance
        self.csv_writer = csv_writer

        # FIXME Not sure if this has to be here
        # Initialize plot window
        self.app = QtGui.QApplication([])
        # self.app = app

        # Plot window configuration
        self.plt = pg.plot()
        self.plt.setWindowTitle('Live Plot from Serial')
        self.plt.setInteractive(True)
        # setting plot window background color to white
        self.plt.setBackground('w')
        self.plt.showGrid(x=True, y=True, alpha=0.3)
        self.plt.setLabel('bottom', 'Time', 's')
        self.plt.setXRange(-10, 0)

        # initialize variables for plotting
        # Plot in chunks, adding one new plot curve for every 100 samples
        self.chunkSize = chunk_size
        # Remove chunks after we have 20
        self.maxChunks = max_chunks

        self.startTime = time.perf_counter()
        # self.startTime = pg.ptime.time() # FIXME This is deprecated and will be removed soon
        self.ptr = 0

        # TODO Ask what is in this 
        self.data_red = np.empty((self.chunkSize + 1, 2))
        self.data_ir = np.empty((self.chunkSize + 1, 2))

        self.curves_red = []
        self.curves_ir = []

        # curve1 = p.plot(pen=(255, 0, 0), name="Red millis curve")
        self.curve_red = self.plt.plot(pen=(0, 255, 0), name="Green sensor_red curve")
        self.curve_ir = self.plt.plot(pen=(0, 0, 255), name="Blue sensor_ir curve")

        # FIXME Should this be really here or in the main()
        # Start the Real Time plotting itself
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(0)

    def update(self):
        # TODO Make the variables class attributes

        # TODO READ THE DATA and FILTER invalid data
        # TODO Refactor this in a separate method
        get_data = self.ser.readline().decode()
        print('get_data= ' + get_data)
        data = get_data.split(',')

        # Filter all non digit characters from the serial reading
        i: int = 0
        for _ in data:
            data[i] = "".join(filter(str.isdigit, data[i]))
            i += 1

        # TODO Make this better
        try:
            millis = int(data[0])
            sensor_red = int(data[1])
            sensor_ir = int(data[2])
        except Exception as e:
            millis = sensor_red = sensor_ir = -1
            print(e)
            print(data)
        # TODO REFACTOR EVERYTHING ABOVE
        print('Millis={}\t Red={}\t IR={}'.format(millis, sensor_red, sensor_ir))

        # Append the current data to the csv
        self.csv_writer.write_row([millis, sensor_red, sensor_ir])

        now = time.perf_counter()
        # now = pg.ptime.time()
        for c in self.curves_red:
            c.setPos(-(now - self.startTime), 0)
        for c in self.curves_ir:
            c.setPos(-(now - self.startTime), 0)

        i = self.ptr % self.chunkSize
        if i == 0:
            self.curve_red = self.plt.plot(pen=(255, 0, 0), name="Red sensor_red curve")
            self.curve_ir = self.plt.plot(pen=(0, 0, 255), name="Blue sensor_ir curve")

            self.curves_red.append(self.curve_red)
            self.curves_ir.append(self.curve_ir)

            last_red = self.data_red[-1]
            last_ir = self.data_ir[-1]

            # data1 = np.empty((chunkSize + 1, 2))
            self.data_red = np.empty((self.chunkSize + 1, 2))
            self.data_ir = np.empty((self.chunkSize + 1, 2))

            # data1[0] = last1
            self.data_red[0] = last_red
            self.data_ir[0] = last_ir

            # FIXME removeItem may cause an error in PySide6
            while len(self.curves_red) > self.maxChunks:
                c = self.curves_red.pop(0)
                self.plt.removeItem(c)
            while len(self.curves_ir) > self.maxChunks:
                c = self.curve_ir.pop(0)
                self.plt.removeItem(c)

        else:
            self.curve_red = self.curves_red[-1]
            self.curve_ir = self.curves_ir[-1]

        self.data_red[i + 1, 0] = now - self.startTime
        self.data_ir[i + 1, 0] = now - self.startTime

        self.data_red[i + 1, 1] = int(sensor_red)
        self.data_ir[i + 1, 1] = int(sensor_ir)

        self.curve_red.setData(x=self.data_red[:i + 2, 0], y=self.data_red[:i + 2, 1])
        self.curve_ir.setData(x=self.data_ir[:i + 2, 0], y=self.data_ir[:i + 2, 1])

        self.ptr += 1

        # This has to be called at the end of the update function to show the new curves
        self.app.processEvents()


def main():
    # User initialization
    baud = 9600

    port = PortScanner.scan()

    ser = serial.Serial(port=port, baudrate=baud, timeout=1)
    ser.flush()
    ser.reset_input_buffer()

    # csv file path
    directory = 'readings/'  # Path of directory where data is been stored
    file_name = 'reading_' + time.strftime('%d-%m-%Y_%H-%M-%S') + '.csv'  # name of the CSV file generated
    file_path = directory + file_name

    csv_writer = CSVWriter(directory, file_path)

    # Create GUI Application

    # app = QtGui.QApplication([])
    # rtp = RealTimePlotter(app=app, serial_conn=ser, csv_writer=csv_writer)
    rtp = RealTimePlotter(app=None, serial_conn=ser, csv_writer=csv_writer)

    timer = QtCore.QTimer()
    timer.timeout.connect(rtp.update)
    timer.start(0)

    # Start GUI
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        app = QtGui.QApplication.instance()
        app.exec()


if __name__ == '__main__':
    main()
