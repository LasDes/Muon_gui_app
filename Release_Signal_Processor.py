
################################################
### Modified 1/1/2019, Dalton Tinoco
### Cosmic watch signal import script
###
### Entry point: import headers here
### Removed imports:
### import numpy as np : Unused
### import json : Unused
################################################
import threading as TH        # For threading functionality for workers
import msvcrt
import serial
import math
import time
import glob
import sys
import signal
import logging
import codecs
import numpy as np
import matplotlib as plt
import array

plt.use("Qt4agg")
import pylab
    
from datetime import datetime
from multiprocessing import Process

MAX_ARRAY_SIZE = 100

class ring_buffer:
    def __init__(self):
        self.data_buffer = np.zeros(MAX_ARRAY_SIZE)[0:-1]
        self.cur_index = 0

    def append(self, in_data):
        if self.cur_index == 99:
            print("spam\n")
        if self.cur_index == 0: # if index position is at head, overwrite head
            self.data_buffer[0] = in_data
            self.cur_index += 1
        elif self.cur_index < MAX_ARRAY_SIZE  - 1: # else if index position is between head and tail (inclusive)
            self.data_buffer[self.cur_index] = in_data # write data to index position
            if self.cur_index == (MAX_ARRAY_SIZE - 1): # if index position is tail, set index to head
                self.cur_index = 0
            else: # else increment by 1
                self.cur_index += 1

    ################################################
    ### Data Collection Worker Function
    ### Responsible for reading signal data from a
    ### USB port, and writing it to a file.
    ###
    ### CHANGES:
    ### removed signal handler, not nessecary for
    ### opening and closing files or opening COMS
    ################################################
def DataCollection(ArduinoPort, fname, id, exitflag, semi, buffer):
    try:
        ComPort = serial.Serial('COM%s' % ArduinoPort) # open the COM Port
        ComPort.baudrate = 9600          # set Baud rate
        ComPort.bytesize = 8             # Number of data bits = 8
        ComPort.parity = 'N'           # No parity
        ComPort.stopbits = 1    
        print("Opening file...\n")

        my_file = open(fname, mode='w', newline="\n")

        counter = 0
        #file.write(str(datetime.now())+ " " + data)
        
        write_to_file = "Detection start time: " + str(datetime.now()) + "\n"
        print(write_to_file)
        my_file.write(write_to_file)
        write_to_file = ' '
        while True:
            if exitflag.locked():
                data = str((ComPort.readline()).decode())   # Wait and read data
                write_to_file = str(datetime.now()) + " : " + data
                my_file.write(write_to_file)
                #add data to stats buffer
                buffer.append(float(data.split()[3]))
                #print("Mean: " + str(np.mean(stats_buffer.data_buffer)) + ", Std: " + str(np.std(stats_buffer.data_buffer)), end='\r')
                semi.acquire()
                time.sleep(0.025)
                semi.release()
            else:
                break

        print("Shutting down open files and ports...\n")
        ComPort.close()     
        my_file.close()
        return True
    except Exception as e:
        print(e)
        print("An error occured... Beats me what it is but it sucks!")
    return True
    
def detection(semi, exitflag):
    filename = "Detection_list.txt"
    counter = 0
    lock_counter = 0
    my_file = open(filename, mode='w', newline="\n")
    print("starting detection...\n")
    while exitflag.locked():
        for s in semi:
            if s.locked():
                lock_counter += 1
        if lock_counter >= len(semi):
            counter += 1
            my_file.write(str(counter) + " " + str(datetime.now()))
        else:
            lock_counter = 0
        time.sleep(0.01)
    my_file.close()

    
# Function Written by: Joshua Hrisko, Engineers Portal webpage
def live_plotter(x_vec, y1_data,line1,identifier = '', pause_time=0.4):
    if line1 == []:
        # this is the call to matplotlib that allows dynamic plotting
        plt.pyplot.ion()
        fig = plt.pyplot.figure(figsize=(10,3))
        ax = fig.add_subplot(111)
        # create a variable for the line so we can later update it
        line1, = ax.plot(x_vec,y1_data,'-o',alpha=0.8)        
        #update plot label/title
        plt.pyplot.ylabel('Y Label')
        plt.pyplot.title('Title: {}'.format(identifier))
        plt.pyplot.show()
    
    # after the figure, axis, and line are created, we only need to update the y-data
    line1.set_ydata(y1_data)
    # adjust limits if new data goes beyond bounds
    if np.min(y1_data)<=line1.axes.get_ylim()[0] or np.max(y1_data)>=line1.axes.get_ylim()[1]:
        plt.pyplot.ylim([np.min(y1_data)-np.std(y1_data),np.max(y1_data)+np.std(y1_data)])
    # this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
    plt.pyplot.pause(pause_time)
    
    # return line so we can update it again in the next iteration
    return line1

################################################
### Thread Container Class
### Responsible for managing thread pool and
### destruction/garbage
###
### CHANGES:
### ADDED: __exit__ method so calls to sys.exit()
### invoke destruction of class instance.
################################################
class ThreadContainer:
    def __init__(self):
    #Member Variables init.
        self.threadpool = []
        self.FileNames = []
        self.port_list = []
        self.lo = TH._allocate_lock()
        self.bank = []
        self.stats_buffer = []
        self.is_started = False

    def start_threads(self):
    # Starts worker threads to collect data
        if not self.is_started:
            self.is_started = True
            self.lo.acquire(False) # acquire lock telling workers not to break current task
            for j in range(0, len(self.port_list)):
                self.bank.append(TH._allocate_lock())
            for i in range(0, len(self.port_list)):
                #print("Starting thread, file: " + NamesList[i] + " Port: " + str(AvailablePorts[i]) + "\n")
                self.stats_buffer.append(ring_buffer())
                t = TH.Thread(target=DataCollection, args=(self.port_list[i], self.FileNames[i], i, self.lo, self.bank[i], self.stats_buffer[i]))
                self.threadpool.append(t)
            for t in self.threadpool:
                t.start() #start all threads
            t = TH.Thread(target=detection, args=(self.bank, self.lo))
            self.threadpool.append(t)
            t.start()
        else:
            print("Already started!")


    def stop_workers(self):
        if self.lo.locked():
            self.is_started = False
            self.lo.release()
            for t in self.threadpool:
                t.join()
            print("Deleting all threads...\n")
            self.threadpool = []
                
    ################################################
    ### Lists serial port names
    ###    :raises EnvironmentError On unsupported or unknown platforms
    ###    :returns A list of the serial ports available on the system
    ################################################
    def serial_ports(self):
        if sys.platform.startswith('win'):
            ports = [(i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
         ports = glob.glob('/dev/tty.*')
        else:
            print("error 1")
            raise EnvironmentError('Unsupported platform')
            sys.exit(0)
        for port in ports:
            try:
                s = serial.Serial('COM%s' % port)
                s.close()
                print(port)
                self.port_list.append(port)
            except (OSError, serial.SerialException):
                pass
        return