from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient('10.114.132.28', port=502)
client.connect()

client.write_coil(15, False)

client.close()
