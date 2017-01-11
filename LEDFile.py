# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 12:32:51 2016

@author: jesse
"""

import numpy as np
from matplotlib import pyplot as plt

class LEDFile:
    def __init__(self, filename):
        bf = BinFile(filename)
        bf.open_bin()
        
        self.data = bf.data
        self.timestamps = [list() for i in range(len(bf.data))]
        
        self.onset_thresh = 0.2
    
        self.colors = ["Blue", "Green", "Teal"]
        self.color_thresholds = [1.5, 3.0, 4.5]
        
        self.get_timestamps()
        
        self.led_codes = list()
                
        self.get_led_codes()
    
    def get_onset(self, chan):
        return [i for i in range(len(chan)-1) if chan[i+1] > self.onset_thresh and chan[i] < self.onset_thresh]
    
    def get_offset(self, chan):
        return [i for i in range(len(chan)-1) if chan[i+1] < self.onset_thresh and chan[i] > self.onset_thresh]
    
    def get_timestamps(self):
        for i in range(len(self.timestamps)):
            self.timestamps[i] = zip(self.get_onset(self.data[i]), self.get_offset(self.data[i]))
    
    def get_step_value(self, chan, index):
        return np.mean(chan[index-50:index+50])
    
    #onset, offset, color, level
    def get_led_codes(self):
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
        
if __name__ == "__main__":
    led = LEDFile('C:/Users/Jesse/Documents/Python Scripts/test/led_test5_data.bin')
    plt.plot(led.data[1])
    plt.plot(led.data[2])