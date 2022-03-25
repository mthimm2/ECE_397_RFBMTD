#!/usr/bin/python3
import serial

class UART_Jetson():

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

        serial_port.write("<Init>".encode())

    def send(self, data):
        # Send data 
        serial_port.write(f"<{data}>".encode())

    # def read(self):
        # serial_port.


# Final FDU Bit structure Implementation

'''
         | Car LEDs  |sys|bat| 
         | L | C | R | S | B | Other Function
 Bit #:  | 0 | 1 | 2 | 3 | 4 |
  L, C, R  => 0, 1, 2, 3     [0=off, 1=close, 2=med, 3=far]
  S => 0, 1                  [0=off, 1=on]
  B => 0, 1, 2, 3, 4         [0=off, 1 : < 25, 2 : >25,  3 : >50, 4 : >75]
  Other Functions => TBD
'''

def EncodeDistanceData(distance, close_coeff, med_coeff, far_coeff):
    data = ""

    if distance > close_coeff:
        data = "1"

    elif distance > med_coeff:
        data = "2"

    elif distance > far_coeff:
        data = "3"

    else:
        data = "0"

    return data

def serial_cleanup():
    serial_port.close()

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

