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
import Jetson.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)

print("UART Demonstration Program")
print("NVIDIA Jetson Nano Developer Kit")
#print(GPIO.JETSON_INFO)
def init():
        
    serial_port = serial.Serial(
        port="/dev/ttyUSB0",
        baudrate=9600,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=5,
    )

    # Wait a second to let the port initialize
    time.sleep(1)
    print('Port', serial_port.port,'Initialized')

    # Send a simple header
    serial_port.write("<Init>".encode())


try:
    # Send a simple header
    serial_port.write("0\r\n".encode())
    
    while True:
        # If the number of bytes in the input buffer is greater than zero 
        if serial_port.inWaiting() > 0:

            x = input("Send: ")
            print(x.encode('utf-8'))
            serial_port.write(x.encode('utf-8'))

            print('waiting for response')
            data = serial_port.read_until()
            data = data.decode('utf-8')
            print("data:", data)

            


except KeyboardInterrupt:
    print("Exiting Program")

except Exception as exception_error:
    print("Error occurred. Exiting Program")
    print("Error: " + str(exception_error))

finally:
    serial_port.close()
    GPIO.cleanup()
    pass
