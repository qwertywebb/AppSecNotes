https://gtfobins.org/

# System

hostname # получить имя хоста
uname -a # получить информацию о ядре
cat /etc/issue # получить информацию о операционной системе
cat /proc/version # получить информацию о ядре и компиляторе

# Processes

ps # список запущенных процессов
ps aux # список запущенных процессов с информацией о пользователях
ps -A # список всех процессов
ps axjd # дерево процессов

# Environment

env # получить список переменных окружения

# Sudo

sudo -l # какие команды можно выполнять от имени root

# Users

whoami # получить имя текущего пользователя
id # получить информацию о текущем пользователе
/etc/passwd | grep "home" # получить информацию о реальных пользователях системы

# Network

ifconfig # получить информацию о сетевых адресах
ip route # получить информацию о маршрутизации сети

netstat -l # Прослушиваемые порты
netstat -tp # Текущие соединения

# Find

find . -name flag1.txt: find the file named “flag1.txt” in the current directory
find /home -name flag1.txt: find the file names “flag1.txt” in the /home directory
find / -type d -name config: find the directory named config under “/”
find / -type f -perm 0777: find files with the 777 permissions (files readable, writable, and executable by all users)
find / -perm a=x: find executable files
find /home -user frank: find all files for user “frank” under “/home”
find / -mtime 10: find files that were modified in the last 10 days
find / -atime 10: find files that were accessed in the last 10 day
find / -cmin -60: find files changed within the last hour (60 minutes)
find / -amin -60: find files accesses within the last hour (60 minutes)
find / -size 50M: find files with a 50 MB size

find / -name flag.txt -type f 2>/dev/null # Поиск файла в корневой директории с удалением ошибок

# Найти SUID(set user id) и SGID(set group id) файлы

find / -perm -u=s -type f 2>/dev/null # Поиск файлов, которые могут запускаться с уровнем привелегий учетной записи с которой они созданы

find / -type f -perm -04000 -ls 2>/dev/null # Если установлен специальный флаг s, программа запускается с правами владельца файла (обычно root)
