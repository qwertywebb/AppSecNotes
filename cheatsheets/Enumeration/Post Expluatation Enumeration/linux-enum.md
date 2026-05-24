## System
# Получить информацию о linux-дистрибутиве
ls /etc/*-release

# Может содержаться информация о users и важные файлы
ls /var/mail

# Узнать установленные приложения
ls /usr/bin
ls /sbin/

# Установленные пакеты на rmp-based системах
rpm -qa

# Установленные пакеты на debian-системах
dpkg -l

## Users
# Кто вошел в систему
who

# Кто вошел в систему и что делает
w

# Кто недавно использовал систему и сколько был онлайн
last

## Networking

# Cетевые интерфейсы
ip address show или кратко ip a s

# Dns-сервер
cat /etc/resolf.conf

# Команда для изучения сетевых подключений 
netstat

-a 	show both listening and non-listening sockets
-l 	show only listening sockets
-n 	show numeric output instead of resolving the IP address and port number
-t 	TCP
-u 	UDP
-x 	UNIX
-p 	Show the PID and name of the program to which the socket belongs

# lsof = list open files ( Часто работает только с sudo)
# В Linux «всё есть файл» — сокеты, порты, соединения — тоже файлы.
lsof -i :80	Кто слушает веб-порт
lsof -i :22	Кто слушает SSH
lsof -i tcp:443	Кто слушает HTTPS (только TCP)
lsof -i @192.168.1.1	Какие соединения идут с IP 192.168.1.1
lsof -i	Все сетевые соединения и слушающие порты
lsof -u brakka	Какие файлы открыл пользователь brakka

## Application/Services

# Запущенные процессы
ps

-e 	all processes
-f 	full-format listing
-j 	jobs format
-l 	long format
-u 	user-oriented format
# ps axjf - иерархия процессов
# a	Показывает процессы всех пользователей (не только текущего)
# x	Показывает процессы, у которых нет терминала (демоны, фоновые службы)
# Без a и x ps показывает только твои процессы, привязанные к терминалу.
ps aux