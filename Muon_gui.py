# Program entry point
from tkinter import *
from tkinter import messagebox
import logging
import copy
import numpy as np
import Release_Signal_Processor as sig


class dual_val:
    def __init__(self, a, b):
        self.val_1 = a
        self.val_2 = b

    def set_a(self, a):
        self.val_1 = a

    def set_b(self, b):
        self.val_2 = b

    def get_a(self):
        return self.val_1

    def get_b(self):
        return self.val_2

class App:
    def __init__(self, main_frame):
        self.root = main_frame
        self.collector = sig.ThreadContainer()
        Main_Label = Label(self.root, text="Cosmic Watch Muon Detector GUI")
        Main_Label.grid(row=0)

        Text_FNAME_one = Label(self.root, text="Output 1 filename")
        Text_FNAME_two = Label(self.root, text="Output 2 filename")
        Text_ports_one = Label(self.root, text="Device 1 Port")
        Text_ports_two = Label(self.root, text="Device 2 Port")

        self.E_FNAME_one = Entry(self.root, textvariable=StringVar())
        self.E_FNAME_two = Entry(self.root)

        self.port_list = []
        self.port_list.append(Listbox(self.root, selectmode=BROWSE, exportselection=False))
        self.port_list.append(Listbox(self.root, selectmode=BROWSE, exportselection=False))

        Ports_Button = Button(self.root, text="Setup Ports", command=self.check_ports)
        Start_Button = Button(self.root, text="Start Detection", bg="green", fg="black", command=self.check_start)
        Stop_Button  = Button(self.root, text="Stop Detection", bg="red", fg="black", command=self.collector.stop_workers)
        S_H_Button   = Button(self.root, text="Show/Hide Graphs", command=self.check_graphing)

        Text_FNAME_one.grid(row=1, sticky=E)
        Text_FNAME_two.grid(row=2, sticky=E)
        Text_ports_one.grid(row=3, sticky=E)
        Text_ports_two.grid(row=4, sticky=E)

        Ports_Button.grid(row=5)

        self.E_FNAME_one.grid(row=1, column=1)
        self.E_FNAME_two.grid(row=2, column=1)

        self.port_list[0].grid(row=3, column=1)
        self.port_list[1].grid(row=4, column=1)

        Start_Button.grid(row=7, column=1)
        Stop_Button.grid(row=7, column=2)
        S_H_Button.grid(row=7, column=3)

    def check_graphing(self):
        x_vec = np.linspace(0, 1, len(self.collector.stats_buffer[0].data_buffer) + 1)[0:-1]
        y_vec = self.collector.stats_buffer[0].data_buffer
        line1 = []
        while True:
            try:
                line1 = sig.live_plotter(x_vec,y_vec,line1)
                y_vec = np.append(y_vec[1:],0.0)
            except:
                pass

    def check_start(self):
        # Set filenames and ports
        if self.E_FNAME_one.get():
            self.collector.FileNames.append(self.E_FNAME_one.get())
        if self.E_FNAME_two.get():
            self.collector.FileNames.append(self.E_FNAME_two.get())
        if (len(self.collector.FileNames) > 0) and (len(self.collector.port_list) > 0):
            self.collector.start_threads()
        elif ((not len(self.collector.FileNames)) > 0) and (len(self.collector.port_list) > 0):
            messagebox.showinfo("Error", "No Filename entered!")
        elif (len(self.collector.FileNames) > 0) and ((not len(self.collector.port_list)) > 0):
            messagebox.showinfo("Error", "No devices connected!")
        else:
            messagebox.showinfo("Error", "No Filename, no devices....")

    def check_ports(self):
        if len(self.collector.port_list):
            for i in range(0, len(self.collector.port_list)):
                self.collector.port_list = []
        self.collector.serial_ports()
        print(self.collector.port_list)
        for lb in self.port_list:
            if lb.size() > 0:
                lb.delete(0, lb.size())
        for p in self.collector.port_list:
            print(p)
            self.port_list[0].insert(END, str(p))
            self.port_list[1].insert(END, str(p))

def main():
    logging.basicConfig(level=logging.DEBUG)
    root = Tk()
    app = App(root)
    app.root.mainloop()

main()



