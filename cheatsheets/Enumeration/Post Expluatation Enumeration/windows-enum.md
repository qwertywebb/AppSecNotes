# Информация о системе 
systeminfo

# Сервисы windows
net start

## Users

# Пользователь и его группы
whoami /groups

# net - инструмент для работы с юзерами, группами и политикой учетной записи

net users - получить список пользователей

net user John - получить информацию о John

net localgroup administrators - получить список администраторов

# Создать пользователя и добавить в группу администраторов:

net user <username> <password> /add

net localgroup administrators <username> /add

## Networking

# Настройки сети
ipconfig /all

# Команда для изучения сетевых подключений 
netstat

# Проверка ip и mac-адресов хостов, которые коммуницировали с текущей системой
arp -a

# Другие утилиты для перебора Windows-машин
# Process Hacker
# Sysinternals Suite
# GhostPack Seatbelt