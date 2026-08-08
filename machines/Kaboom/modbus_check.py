from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient('10.114.132.28', port=502)
client.connect()

for i in range(10):
    result = client.read_holding_registers(i)
    if result.registers:
        print(f"Register {i}: {result.registers[0]}")

client.close()