import smbus
import time
from datetime import datetime
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import json
# Get I2C bus
bus = smbus.SMBus(1)

client = mqtt.Client()
client.username_pw_set(username="pi", password="Helsinki2017")
client.connect("192.168.1.100", 1883, 600)
print('Connected to MQTT')

while True:
    try:
		# MCP9808 address, 0x18(24)
		# Select configuration register, 0x01(1)
		#		0x0000(00)	Continuous conversion mode, Power-up default
        config = [0x00, 0x00]
        bus.write_i2c_block_data(0x18, 0x01, config)
		# MCP9808 address, 0x18(24)
		# Select resolution rgister, 0x08(8)
		#		0x03(03)	Resolution = +0.0625 / C
        bus.write_byte_data(0x18, 0x08, 0x03)

        time.sleep(0.5)

		# MCP9808 address, 0x18(24)
		# Read data back from 0x05(5), 2 bytes
		# Temp MSB, TEMP LSB
        data = bus.read_i2c_block_data(0x18, 0x05, 2)

		# Convert the data to 13-bits
        ctemp = ((data[0] & 0x1F) * 256) + data[1]
        if ctemp > 4095 :
            ctemp -= 8192
        ctemp = ctemp * 0.0625

		# Output data to screen
        print (str(datetime.now()) , " Temperature in Celsius is    : %.2f C" %ctemp )
        payload = { "temperature": round(ctemp,2) } 
        client.publish("mcp9808/", json.dumps(payload))
        time.sleep(60)
    except KeyboardInterrupt:
        # When Ctrl+C is pressed execution of the while loop is stopped
        print('Exit')
        break
