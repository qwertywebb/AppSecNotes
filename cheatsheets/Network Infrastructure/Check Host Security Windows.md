# Перечислить антивирусное программное обеспечение
Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct

# Windows Defender

# Проверить статус(running,stop,disable)
Get-Service WinDefend

# Проверить опции Антивируса
Get-MpComputerStatus | select RealTimeProtectionEnabled

# Проверка наличия firewall, который разрешает или блокирует отправку пакетов.
Get-NetFirewallProfile | Format-Table Name, Enabled

# Если имеем привелегии админа может попробовать отключить профили firewall
Set-NetFirewallProfile -Profile Domain, Public, Private -Enabled False

# Проверить текущие правила firewall
Get-NetFirewallRule | select DisplayName, Enabled, Description

# Обычно в красной команде мы понятия не имеем, что блокирует firewall, поэтому можно попробовать подключиться к внутреннему сервису, чтобы понять позволяет ли firewall устанавливать соединение
Test-NetConnection -ComputerName 127.0.0.1 -Port 80
или
(New-Object System.Net.Sockets.TcpClient("127.0.0.1", "80")).Connected

# Получить список логов, иногда это поможет определить сервисы и приложения установленные в системе
Get-EventLog -List

# Sysmon - утилита, которая собирает и регистрирует различные логи в системе.
# Проверить её наличие
Get-Process | Where-Object { $_.ProcessName -eq "Sysmon" }

# Host-based Intrusion Detection/Prevention System (HIDS/HIPS)
# Это ПО, которая мониторит необычные и злонамеренные активности.
# HIPS включает в себя много функций антивируса, мониторинга, firewall и др.

#  Endpoint Detection and Threat Response (EDTR) - это следующее поколения антивирусов, которое в режиме реального времени отслеживает вредоносную активность.

# Для перечисления ПО на машине осуществляющего защитную деятельность используются утилиты:
# EDRChecker - https://github.com/PwnDexter/Invoke-EDRChecker
# SharpEDRChecker - https://github.com/PwnDexter/SharpEDRChecker