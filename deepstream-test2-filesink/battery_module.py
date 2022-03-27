#!/usr/bin/env python
import struct
import smbus
import sys
import time

def readVoltage(bat_bus):
    address = 0x36
    
    try:
        read = bat_bus.read_word_data(address, 2)
        swapped = struct.unpack("<H", struct.pack(">H", read))[0]
        voltage = swapped * 1.25 / 1000 / 16
    except: 
        voltage = 0
    
    return voltage

def readCapacity(bat_bus):
    address = 0x36
    try:
        read = bat_bus.read_word_data(address, 4)
        swapped = struct.unpack("<H", struct.pack(">H", read))[0]
        capacity = swapped / 256
    except:
        capacity = 0
    return capacity

if __name__ == "__main__":
    bat_bus = smbus.SMBus(1) # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

    while True:
        print("******************")
        print("Voltage:%5.2fV" % readVoltage(bat_bus))

        print("Battery:%5i%%" % readCapacity(bat_bus))

        if readCapacity(bat_bus) == 100:
            print("Battery FULL")

        if readCapacity(bat_bus) < 20:
                print("Battery LOW")
				
        print("******************")
        time.sleep(2)
