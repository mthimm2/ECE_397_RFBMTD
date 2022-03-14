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

print("UART Demonstration Program")
print("NVIDIA Jetson Nano Developer Kit")


serial_port = serial.Serial(
    port="/dev/ttyTHS1",
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)
# Wait a second to let the port initialize
time.sleep(1)

# Make the data a queue
# Not sure what more we're gonna have in here, but we can have a list of lists that we treat like a queue
# Come time to write, we can prepare any number of 
data = [[] * 2]

try:
    # Send a simple header
    serial_port.write("UART Demonstration Program\r\n".encode())
    serial_port.write("NVIDIA Jetson Nano Developer Kit\r\n".encode())
    while True:
        if serial_port.inWaiting() > 0:

            # Take the data we've received and throw it into a queue
            data.append(serial_port.read()) # data = serial_port.read()
            print(data)

            # This line just regurgitates what someone is typing on the other end in their demo
            #serial_port.write(data)
            
            # if we get a carriage return, add a line feed too
            # \r is a carriage return; \n is a line feed
            # This is to help the tty program on the other end 
            # Windows is \r\n for carriage return, line feed
            # Macintosh and Linux use \n
            #if data == "\r".encode():
                # For Windows boxen on the other end
                #serial_port.write("\n".encode())
        
        # The above block appears to take in one character at a time.
        for char in data:
            print(char, end = '')
        print('')

except KeyboardInterrupt:
    print("Exiting Program")

except Exception as exception_error:
    print("Error occurred. Exiting Program")
    print("Error: " + str(exception_error))

finally:
    serial_port.close()
    pass