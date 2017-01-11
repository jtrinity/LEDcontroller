# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 14:07:57 2016

@author: Jesse Trinity (Coleman Lab)
"""

import Tkinter as tk
import tkFileDialog

import numpy as np
from matplotlib import pyplot as plt

import csv as csv
import time
import random

from pyfirmata import Arduino, util, serial
import serial.tools.list_ports

g_led = None

class PhantomController:
    #Simulates Arduino pin functions
    #Used when no cotroller is connected
    def __init__(self):
        pass
    def get_pin(self, s):
        return PhantomPin()
    def exit(self):
        pass

class PhantomPin:
    #Pin for PhantomController class
    def __init__(self):
        pass
    def read(self):
        return 0.0
    def write(self, f):
        pass
        
#Open serial port
ports = list(serial.tools.list_ports.comports())
connected_device = None
for p in ports:
    if 'Arduino' in p[1]:
        try:
            board = Arduino(p[0])
            connected_device = p[1]
            print "Connected to Arduino"
            print connected_device
            break
        except serial.SerialException:
            print "Arduino detected but unable to connect to " + p[0]
if connected_device == None:
    for p in ports:
        if 'ttyACM' in p[0]:
            try:
                board = Arduino(p[0])
                connected_device = p[1]
                print "connected"
                break
            except serial.SerialException:
                pass

if connected_device is not None:
    it = util.Iterator(board)
    it.start()
    board.analog[0].enable_reporting()
elif connected_device is None:
    print "No connected Arduino - timestamp data will be text only"
    board = PhantomController()
    
#Timestamp Pins
pin_a = board.get_pin('d:3:p') # low-pass filter with 4.7uF, x resistor btwn pin and (+) of cap (- cap to gnd); OUT @ res-cap+
pin_b = board.get_pin('d:6:p')

#LED Pins
Green = board.get_pin('d:9:p')
Blue = board.get_pin('d:10:p')


    
#-----WIDGETS-----

class Window(tk.Toplevel):
    #Generic window framework - provides mutual lifting and controlling with root window
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.bind("<FocusIn>", self.parent.on_focus_in)
        
        if ('title' in kwargs):
            self.title(kwargs['title'])
            
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    
    def on_closing(self):
    #kill root when this window is closed
        self.parent.destroy()
        

class Button(tk.Button):
    #Generic *gridded* button framework
    def __init__(self, container, name, command, position):
        button = tk.Button(container, text = name, command = command)
        button.grid(row = position[0], column = position[1], padx = 5, pady  = 5, sticky = tk.N+tk.S+tk.E+tk.W)
        
     
#-----Main Application-----
class MainApp(tk.Tk):
    def __init__(self, master = None, *args, **kwargs):
        tk.Tk.__init__(self, master, *args, **kwargs)
        self.title("LED Controller")
        
        #populate windows by (class, name)
        self.windows = dict()
#        for (C, n) in ((window_one, "window 1"), (window_two,"window 2")):
        for (C, n) in ():
            window = C(self, title = n)
            self.windows[C] = window
        
        self.bind("<FocusIn>", self.on_focus_in)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
                
        #create windows by name
#        window_names = ("window1", "window2")
#        windows = {name:Window(self.root, title = name) for name in window_names}
                
               
        #-----class widgets-----
        #labels
        self.title_frame= tk.Frame(self)
        self.title_frame.pack(side = "top")
        
        self.title_label = tk.Label(self.title_frame, text = "Toolbar")
        self.title_label.grid(row = 0, column = 0)
        
        #Buttons
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side = "top")
        
        self.load_button = Button(self.button_frame, "load file", self.load, (1,0))
                
        self.button1 = Button(self.button_frame, "Run LED Experiment", self.color_trial, (1,1))
        
        self.button2 = Button(self.button_frame, "Abort", self.abort_run, (1,2))
        
        self.button3 = Button(self.button_frame, "button 3", self.default_onclick, (1,3))
        
        #Save Option
        self.save_frame = tk.Frame(self).pack(side = "top")
        self.save_option = tk.IntVar()
        self.save_option.set(0)
        self.save_box = tk.Checkbutton(self.save_frame, text = "Save trials to txt file", variable = self.save_option).pack()
        
        #Color Options
        self.colors_frame = tk.Frame(self)
        self.colors_frame.pack(side = "top")
        
        self.blue_option_var = tk.IntVar()
        self.blue_option_var.set(1)
        self.blue_option = tk.Checkbutton(self.colors_frame, text = "Blue", variable = self.blue_option_var).grid(row = 0, column = 0)
                
        self.green_option_var = tk.IntVar()
        self.green_option_var.set(1)
        self.green_option = tk.Checkbutton(self.colors_frame, text = "Green", variable = self.green_option_var).grid(row = 0, column = 1)
                
        self.cyan_option_var = tk.IntVar()
        self.cyan_option_var.set(1)
        self.cyan_option = tk.Checkbutton(self.colors_frame, text = "Cyan", variable = self.cyan_option_var).grid(row = 0, column = 2)
        
        #Fields
        self.fields_frame = tk.Frame(self)
        #self.fields_frame.columnconfigure(1, weight = 1)
        #self.fields_frame.columnconfigure(0, weight = 3)
        self.fields_frame.pack(side = "top")
        
        self.name_label = tk.Label(self.fields_frame, text = "Trial Name (optional)").grid(row = 0, column = 0, stick = tk.W, padx = 10, pady = 10)
        self.name_string = tk.StringVar()
        self.name_string.set("exp_1")
        self.name_entry = tk.Entry(self.fields_frame, textvariable = self.name_string).grid(row = 0, column = 1, stick = tk.W, padx = 10, pady = 10)
        
        #luminance levels
        self.levels_label = tk.Label(self.fields_frame, text = "Luminance Levels (0-1)").grid(row = 1, column = 0, stick = tk.W, padx = 10, pady = 10)
        self.levels_string = tk.StringVar()
        self.levels_string.set("0.3, 0.6, 0.9")
        self.levels_entry = tk.Entry(self.fields_frame, textvariable = self.levels_string).grid(row = 1, column = 1, stick = tk.W, padx = 10, pady = 10)
        
        #Number of trials
        self.trials_label = tk.Label(self.fields_frame, text = "Trial Count (each stim)").grid(row = 2, column = 0, stick = tk.W, padx = 10, pady = 10)
        self.trials_string = tk.StringVar()
        self.trials_string.set("20")
        self.trials_entry = tk.Entry(self.fields_frame, textvariable = self.trials_string).grid(row = 2, column = 1, stick = tk.W, padx = 10, pady = 10)
        
        #flash duration
        self.duration_label = tk.Label(self.fields_frame, text = "Flash Duration (s)").grid(row = 3, column = 0, stick = tk.W, padx = 10, pady = 10)
        self.duration_string = tk.StringVar()
        self.duration_string.set("0.1")
        self.duration_entry = tk.Entry(self.fields_frame, textvariable = self.duration_string).grid(row = 3, column = 1, stick = tk.W, padx = 10, pady = 10)
        
        #flash interval
        self.interval_label = tk.Label(self.fields_frame, text = "Interval Duration (s)").grid(row = 4, column = 0, stick = tk.W, padx = 10, pady = 10)
        self.interval_string = tk.StringVar()
        self.interval_string.set("10.0")
        self.interval_entry = tk.Entry(self.fields_frame, textvariable = self.interval_string).grid(row = 4, column = 1, stick = tk.W, padx = 10, pady = 10)
        
        #Start delay
        self.delay_label = tk.Label(self.fields_frame, text = "Start Delay (s)").grid(row = 5, column = 0, stick = tk.W, padx = 10, pady = 10)
        self.delay_string = tk.StringVar()
        self.delay_string.set("5.0")
        self.delay_entry = tk.Entry(self.fields_frame, textvariable = self.delay_string).grid(row = 5, column = 1, stick = tk.W, padx = 10, pady = 10)
        
        #Arduino info
        self.arduino_frame = tk.Frame(self)
        self.arduino_frame.pack(side = "top")
        self.arduino_label = tk.Label(self.arduino_frame, text = connected_device)
        self.arduino_label.pack(side = "bottom")
        

        #-----end widgets-----
        
        #variables
        self.file_list = list()
        self.filedata = list()
        
        #experiment variables
        self.num_trials = 30
        self.duration = 0.1
        self.start_delay = 5.0
        
        #Indicates the Luminance level of the LEDs
        self.color_levels = [0.2, 0.50, 1.0] #color codes 0,1,2
        
        #self.level_code = [0.1, 0.2, 0.3] #level codes 0,1,2
        #color codes : (0, green), (1, blue), (2, cyan)
        self.colors = ["green", "blue", "cyan"]
        self.options = [0,1,2]
        self.relaxation = 1  #seconds
        
        self.last_trials = []
        
        self.led = None
        
        #-----FLAGS-----
        
        self.ABORT = tk.BooleanVar()
        self.ABORT.set(False)
        #-----end-----
        
        #set root window position (needs to happen last to account for widget sizes)
        self.update()
        self.hpos =  self.winfo_screenwidth()/2 - self.winfo_width()/2
        self.vpos = 0
        self.geometry("+%d+%d" % (self.hpos, self.vpos))
        
        self.mainloop()
    
    def abort_run(self):
        #Set abort flag - replace with intercept?
        self.ABORT = True
        
    #Experiment Functions
    def write_color(self, color, level):
        #Turns on led and writes timestamp pins. Returns write time.
        start = time.time()
        color = self.colors[color]
        if color == "green":
            Green.write(self.color_levels[level])
            pin_a.write(0.3)
            
        elif color == "blue":
            Blue.write(self.color_levels[level])
            pin_a.write(0.6)
        elif color == "teal":
            Green.write(self.color_levels[level])
            Blue.write(self.color_levels[level])
            pin_a.write(0.9)
        pin_b.write(1.0)
        return start

    def color_trial(self):
        #Runs a random sampling from the given colors and levels
        print "Running " + str(self.name_string.get())
        self.ABORT = False
        
        #Get field options
        self.start_delay = self.get_num_field(self.delay_string)[0]
        self.num_trials = int(self.get_num_field(self.trials_string)[0])
        self.color_levels = self.get_num_field(self.levels_string)
        #self.level_code = [0.1 * (i + 1) for i in range(len(self.color_levels))]
        self.relaxation = self.get_num_field(self.interval_string)[0]
        self.duration = self.get_num_field(self.duration_string)[0]
        
        options = []
        if self.green_option_var.get() == 1:
            options.append(0)
        if self.blue_option_var.get() == 1:
            options.append(1)
        if self.cyan_option_var.get() == 1:
            options.append(2)
        try:
            levels_indices = [i for i in range(len(self.color_levels))]
        except TypeError:
            print "Enter at least 1 luminance level"
            return
        colors_list = self.make_rand_list(self.num_trials, options, levels_indices)
        trials = []
        
        pin_a.write(0.0)
        pin_b.write(0.0)
        Green.write(0.0)
        Blue.write(0.0)
        
        wait_time = time.time()
        while (time.time()- wait_time < self.start_delay):
            pass
        
        
        for trial in range(len(colors_list)):
            
            #Get random trial
            color = colors_list[trial][0]
            level = colors_list[trial][1]
            
            trials.append([color,level,time.time()-wait_time])
            start = self.write_color(color, level)
            
            #Wait out duration
            while(time.time()-start < self.duration):
                pass
            pin_b.write(0.0)
            Green.write(0.0)
            Blue.write(0.0)
            
            #Writes color and level codes for 500ms each
            while(time.time() - start <0.5):
                pass
            pin_a.write(self.color_levels[level])
            while(time.time() - start <1.0):
                pass
            pin_a.write(0.0)
            
            print [self.colors[color], self.color_levels[level]]
            
            #Wait out relxation time
            while(time.time() - start < self.relaxation + self.duration):
                if self.ABORT == True:
                    self.ABORT = False
                    print "Aborted"
                    return
                self.update()

        self.last_trials = trials
        if self.save_option.get() == 1:
            self.save_trials()
        print "Done"
    
    def get_num_field(self, field):
        field_entry = field.get()
        entries = field_entry.split(',')
        num_entries = []
        for entry in entries:
            try:
                num_entry = float(entry)
            except ValueError:
                print "Bad entry field value"
                return None
            num_entries.append(num_entry)
        return num_entries
    
    def make_rand_list(self, repetitions, options, levels):
        #get randomized list of options for repetitions times
        r_list = []
        for option in options:
            for level in levels:
                r_list.append((option, level))
        r_list = r_list * repetitions
        random.shuffle(r_list)
        return r_list
    
    def save_trials(self):
        with open(self.name_string.get() + '.txt', 'w+') as fn:
            fn.seek(0)

            fn.write("name: " + str(self.name_string.get()) + "\n")
            fn.write("luminance levels: " + str(self.color_levels) + "\n")
            fn.write("trial count: " + str(self.num_trials) + "\n")
            fn.write("flash duration: " + str(self.duration) + "\n")
            fn.write("interval duration: " + str(self.relaxation) + "\n")
            fn.write("start_delay: " + str(self.start_delay) + "\n")
            fn.write("\n")
            fn.write("color, luminance, voltage \n")
            for trial in self.last_trials:
                fn.write(str(trial[2]) + "," + str(self.colors[trial[0]]) +","+ str(self.color_levels[trial[1]]) + "\n")
            fn.truncate()

    
    #Dummy command function
    def default_onclick(self):
        print "widget pressed"
    
    #Dummy event function
    def default_on_event(self):
        print "event detected"
        
    def on_focus_in(self, event):
        self.lift()
        for win in self.windows:
            self.windows[win].lift()
    
    #Open a file dialog and record selected filenames to self.file_names
    def load(self):
        global g_led
        files = tkFileDialog.askopenfilenames()
        self.file_list = list(files)
        for f in self.file_list:
            self.led = LEDFile(f)
            #self.filedata.append(led)
            plt.plot(self.led.data[1])
            plt.plot(self.led.data[2])
            target = f[:-3] + "csv"
            with open(target, 'w+') as fn:
                fn.seek(0)
                w=csv.writer(fn, delimiter = ',', lineterminator = "\n")
                for i in range(len(self.led.led_codes)):
                    code = self.led.led_codes[i]
                    w.writerow(code)
                fn.truncate()
        g_led = self.led
        
    
    def file_to_array(self, fn):
        with open(fn, 'rb') as open_file:
            self.data.append(np.array(open_file))
    
    def csv_to_array(self, fn):
        with open(fn, 'rb') as csv_file:
            reader = csv.reader(csv_file, delimiter = ',')
            self.filedata.append(np.array(reader))
            
    def on_closing(self):
        board.exit()
        self.destroy()

class LEDFile:
    #Opens and graphs bin file from NeuroGUI
    def __init__(self, filename):
        bf = BinFile(filename)
        bf.open_bin()
        
        self.data = bf.data
        self.timestamps = [list() for i in range(len(bf.data))]
        
        self.onset_thresh = 0.2
        
        self.colors = ["Green", "Blue", "Teal"]
        self.color_thresholds = [1.5, 3.0, 4.5] #0.3, 0.6, 0.9 scaled to 5V arduino
        
        self.get_timestamps()
        
        self.led_codes = list()
                
        self.get_led_codes()
    
    def get_onset(self, chan):
        #gets onset of strobe according to specified threshold
        return [i for i in range(len(chan)-1) if chan[i+1] > self.onset_thresh and chan[i] < self.onset_thresh]
    
    def get_offset(self, chan):
        #gets onset of strobe according to specified threshold
        return [i for i in range(len(chan)-1) if chan[i+1] < self.onset_thresh and chan[i] > self.onset_thresh]
    
    def get_timestamps(self):
        #gives the onset, offset of strobe channel
        for i in range(len(self.timestamps)):
            self.timestamps[i] = zip(self.get_onset(self.data[i]), self.get_offset(self.data[i]))
    
    def get_step_value(self, chan, index):
        #samples 100 ms of step channel follwing strobe offset
        return np.mean(chan[index-50:index+50])
    
    def get_led_codes(self):
        #creates led code tuples (onset, offset, color, level)
        for stamp in self.timestamps[1]:
            color_value = self.get_step_value(self.data[2], stamp[1] + 250)
            level = self.get_step_value(self.data[2], stamp[1] + 750)
            
            vals = np.abs(np.array(self.color_thresholds) - color_value)
            color = self.colors[np.argmin(vals)]
            
            self.led_codes.append((stamp[0], stamp[1], color, level))
        
            
class BinFile:
    def __init__(self, filename):
        self.totalChannels = 8
        self.filename = filename
        self.dataType = '<d'
        self.data = [0]
        
        #filename = '4031B_45deg_Day1_data.bin'
        #totalChannels = 8

    def setTotalChannels(self, n):
        self.totalChannels = n

    def setFilename(self, name):
        self.filename = name

    def setDataType(self, dt):
        self.dataType = dt

    def open_bin(self):
        
        self.data = np.fromfile(str(self.filename), dtype = np.dtype(self.dataType))
        #truncate the data file to handle bad input
        while(len(self.data) % self.totalChannels != 0):
            self.data = self.data[0:len(self.data)-1]
        self.data = self.data.reshape(len(self.data)/self.totalChannels, self.totalChannels)
        self.data = np.transpose(self.data)

              
#-----Windows-----
#Left Window
class window_one(Window):
    def __init__(self, parent, *args, **kwargs):
        Window.__init__(self, parent, *args, **kwargs)
        #self.title("Window One")
        #Set window position (needs to happen last to account for widget sizes)
        #self.geometry("+%d+%d" % (0, 0))
        self.update()
        self.hpos = 0
        self.vpos = self.winfo_screenheight()/2 - self.winfo_height()/2
        self.geometry("+%d+%d" % ( self.hpos, self.vpos))

#Right Window
class window_two(Window):
    def __init__(self, parent, *args, **kwargs):
        Window.__init__(self, parent, *args, **kwargs)
        #set window position (needs to happen last to account for widget sizes)
        #self.geometry("+%d+%d" % (0, 0))
        self.update()
        self.hpos =  self.winfo_screenwidth() - self.winfo_width()
        self.vpos = self.winfo_screenheight()/2 - self.winfo_height()/2
        self.geometry("+%d+%d" % (self.hpos, self.vpos))


MainApp()
