from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient('10.114.132.28', port=502)
client.connect()

for i in range(20):
    result = client.read_coils(i)
    if result.bits:
        print(f"Coil {i}: {result.bits[0]}")

client.close()
