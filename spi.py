import spidev

spi_bus = 0
spi_device = 0

spi = spidev.SpiDev()
spi.open(spi_bus, spi_device)
spi.max_speed_hz = 1000000

# send a null byte to check for value
send_byte = 0x80
print("sent byte: " + str(send_byte))

rcv_byte = spi.xfer2([send_byte])   # send & receive
print("receieved byte" + str(rcv_byte))

