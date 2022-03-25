'''
The stock Jetson Nano starts a console on the ttyTHS1 serial port at startup through a service. 
The script that starts the service is nvgetty.sh which launches getty. The script is located in /etc/systemd. 
While this does not conflict with the script presented here, consider disabling the console if you are using the serial port to avoid conflicts. 
Note that normal udev rules will be overridden by the console while the service is running. To disable the console:

$ systemctl stop nvgetty
$ systemctl disable nvgetty
$ udevadm trigger
# You may want to reboot instead - Not sure what this part means yet

Install the py-serial library:
$ sudo apt-get install python3-serial

Pinout:
Jetson Pins Used:
Pin 6 - GND
Pin 8 - D14 - TXD (Plugs into Arduino RX)
Pin 10 - D15 - RXD (Plugs into Arduino TX)

Forum threads that may help:
https://forums.developer.nvidia.com/t/unreliable-serial-communcation-via-the-uart-tx-rx-gpio-pins/158249/10 - Long thread with mod helping
https://github.com/tymancjo/jetson_trials/blob/main/Pose_M.py - Guy who uses UART to communicate with Arduino

Arduino References:
https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7766-8-bit-AVR-ATmega16U4-32U4_Datasheet.pdf
https://github.com/arduino-c/uart/blob/master/uart.c
'''

#!/usr/bin/python3
import time
import serial

class UART_Jetson():
    '''
    Pinout:
    Jetson Pins Used:
    Pin 6 - GND
    Pin 8 - D14 - TXD (Plugs into Arduino RX)
    Pin 10 - D15 - RXD (Plugs into Arduino TX)
    '''

    def __init__(self):
        # https://pyserial.readthedocs.io/en/latest/pyserial_api.html?highlight=byte_size#serial.Serial.inter_byte_timeout
        serial_port = serial.Serial(
            port="/dev/ttyUSB0",
            baudrate=9600,
            bytesize=serial.EIGHTBITS,      # FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS
            parity=serial.PARITY_NONE,      # PARITY_NONE, PARITY_EVEN, PARITY_ODD PARITY_MARK, PARITY_SPACE 
            stopbits=serial.STOPBITS_ONE,   # STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO
            timeout=5,
        )        

        # Wait a second to let the port initialize
        time.sleep(1)

    def send(self, data):
        # Send data 
        serial_port.write(f"<{data}>".encode())




# Final FDU Implementation

'''
  L | C | R | S | B | Other Function
  0 | 1 | 2 | 3 | 4 |
  L, C, R  => 0, 1, 2, 3     [0=off, 1=close, 2=med, 3=far]
  S => 0, 1                  [0=off, 1=on]
  B => 0, 1, 2, 3, 4         [0=off, 1 : < 25, 2 : >25,  3 : >50, 4 : >75]
  Other Functions => TBD
'''

def EncodeDistanceData(distance, close_coeff, med_coeff, far_coeff):
    data = ""

    if distance > close_coeff:
        data = "2"

    elif distance > med_coeff:
        data = "3"

    elif distance > far_coeff:
        data = "4"

    else:
        data = "1"

    return data

# Max
# 00 = off, 01 = far, 10 = med, 11 = close
# Function to determine which LED to turn on
# def EncodeDistanceData(distance, close_coeff, med_coeff, far_coeff):
#     data = ""

#     if distance > close_coeff:
#         data = "11"

#     elif distance > med_coeff:
#         data = "10"

#     elif distance > far_coeff:
#         data = "01"

#     else:
#         data = "00"

#     return data


# Eric
# Function to determine which LED to turn on
# def EncodeDistanceData(distance, close_coeff, med_coeff, far_coeff):
#     data = ""
#     if distance > close_coeff:
#         data += "1"
#     else:
#         data += "0"

#     if distance > med_coeff:
#         data += "1"
#     else:
#         data += "0"      

#     if distance > far_coeff:
#         data += "1"
#     else:
#         data += "0"    

#     return data


'''
    Example:
        UART_Jetson_Object = UART_Jetson()
        
        dataLeft = EncodeDistanceData(distance, close_coeff, med_coeff, far_coeff)
        dataCenter = EncodeDistanceData(distance, close_coeff, med_coeff, far_coeff)
        dataRight = EncodeDistanceData(distance, close_coeff, med_coeff, far_coeff)
        dataOther = "000"   # status, battery, setup

        UART_Jetson_Object.send(dataLeft + dataCenter + dataRight + dataOther)
'''

