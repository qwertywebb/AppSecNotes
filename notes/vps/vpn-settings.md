# 🚀 Полный отчет по созданию защищенного VPN-сервера

## 📋 Оглавление
1. [Базовая настройка сервера](#-1-базовая-настройка-сервера)
2. [Настройка безопасности](#-2-настройка-безопасности)
3. [Установка S-UI панели](#-3-установка-s-ui-панели)
4. [Настройка домена и SSL](#-4-настройка-домена-и-ssl)
5. [Создание VPN подключения](#-5-создание-vpn-подключения)
6. [Настройка клиента](#-6-настройка-клиента)
7. [Проверка работы](#-7-проверка-работы)


## 🔒 1. Базовая настройка сервера

### 1.1 Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Создание пользователя
```bash
# Создаем пользователя для безопасной работы
adduser brakka

### 1.3 Настройка SSH-ключа
```bash
# Генерация SSH-ключа (на клиентской машине)
ssh-keygen -t ed25519 -C "brakka@gmail.com"

# Копирование ключа на сервер
ssh-copy-id brakka@IP_СЕРВЕРА

# Подключение по ключу
ssh brakka@IP_СЕРВЕРА
```


## 🛡️ 2. Настройка безопасности

### 2.1 Защита SSH
```bash
sudo nano /etc/ssh/sshd_config
```

Внесите изменения:
```ini
PermitRootLogin no          # Запрет входа для root
PasswordAuthentication no   # Отключение входа по паролю
UsePAM no                  # Отключение PAM
```

Примените изменения:
```bash
sudo systemctl restart ssh
```

### 2.2 Настройка брандмауэра (UFW)
```bash
# Открываем необходимые порты
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS

# Включаем брандмауэр
sudo ufw enable

# Проверяем статус
sudo ufw status verbose
```

### 2.3 Настройка Fail2Ban
```bash
# Установка
sudo apt install fail2ban -y

# Настройка
sudo nano /etc/fail2ban/jail.local
```

Добавьте конфигурацию:
```ini
[DEFAULT]
bantime = 3600          # Блокировка на 1 час
findtime = 600          # Окно в 10 минут
maxretry = 5            # 5 попыток до блокировки
ignoreip = 127.0.0.1/8 ::1 46.181.20.34  # Ваш IP

[sshd]
enabled = true
maxretry = 3            # 3 попытки для SSH
bantime = 7200          # Блокировка на 2 часа
```

Проверка и запуск:
```bash
# Проверка конфигурации
sudo fail2ban-client -t

# Перезапуск
sudo systemctl restart fail2ban

# Проверка статуса
sudo fail2ban-client status sshd
```


## 🖥️ 3. Установка S-UI панели

### 3.1 Установка панели
```bash
# Установка curl
sudo apt update && sudo apt install -y curl

# Установка S-UI
bash <(curl -Ls https://raw.githubusercontent.com/alireza0/s-ui/master/install.sh)
```

### 3.2 Открытие портов панели
```bash
# Порты для панели и подписки
sudo ufw allow 2095/tcp   # Веб-интерфейс
sudo ufw allow 2096/tcp   # Подписка

# Открываем порт для VPN
sudo ufw allow 443/tcp
sudo ufw allow 443/udp    # Hysteria2 использует UDP
```

### 3.3 Вход в панель
```
http://<IP_СЕРВЕРА>:2095/app/
```


## 🌐 4. Настройка домена и SSL

### 4.1 Регистрация домена на DuckDNS
1. Перейдите на [duckdns.org](https://www.duckdns.org)
2. Войдите через Google/GitHub
3. Создайте домен: `x.duckdns.org`
4. Сохраните токен

### 4.2 Установка Certbot
```bash
# Установка snap
sudo apt update && sudo apt install -y snapd

# Установка Certbot
sudo snap install core
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

### 4.3 Получение SSL-сертификата
```bash
# Останавливаем службы, использующие порт 443
sudo systemctl stop sing-box 2>/dev/null
sudo systemctl stop nginx 2>/dev/null
sudo systemctl stop apache2 2>/dev/null

# Получение сертификата
sudo certbot certonly --standalone \
  --register-unsafely-without-email \
  --non-interactive \
  --agree-tos \
  -d x.duckdns.org

# Проверка сертификата
sudo ls -la /etc/letsencrypt/live/x.duckdns.org/
```

Файлы сертификата:
- `fullchain.pem` - полная цепочка сертификатов
- `privkey.pem` - приватный ключ


## 🔗 5. Создание VPN подключения

### 5.1 Настройка Inbound в S-UI
1. Войдите в панель S-UI
2. Перейдите в **"Inbounds"** → **"Add Inbound"**
3. Заполните параметры:

| Параметр | Значение |
|----------|----------|
| **Protocol** | `Hysteria2` |
| **Port** | `443` |
| **Domain** | `brk-france.duckdns.org` |
| **SNI** | `brk-france.duckdns.org` |
| **Certificate** | `/etc/letsencrypt/live/brk-france.duckdns.org/fullchain.pem` |
| **Private Key** | `/etc/letsencrypt/live/brk-france.duckdns.org/privkey.pem` |
| **Password** | Сгенерируйте сложный пароль |

### 5.2 Создание клиента
1. Перейдите в **"Clients"** → **"Add Client"**
2. Заполните:

| Параметр | Значение |
|----------|----------|
| **Inbound** | Выберите созданный Hysteria2 |
| **Email** | `brakka-windows` |
| **Remark** | `Windows 11` |
| **Total GB** | `0` (безлимит) |

3. Нажмите **"Add"**
4. Скопируйте ссылку подключения (иконка "Share")

### 5.3 Перезапуск службы
```bash
sudo systemctl restart s-ui
```


## 💻 6. Настройка клиента

### 6.1 Установка v2rayN
1. Скачайте v2rayN с [GitHub](https://github.com/2dust/v2rayN/releases)
2. Установите и запустите

### 6.2 Импорт конфигурации
**Автоматический импорт:**
- Скопируйте ссылку из панели S-UI
- В v2rayN: **"Сервер"** → **"Импортировать URL из буфера обмена"**

**Ручная настройка (если импорт не работает):**

| Параметр | Значение |
|----------|----------|
| **Address** | `brk-france.duckdns.org` |
| **Port** | `443` |
| **Password** | Пароль из Inbound |
| **SNI** | `brk-france.duckdns.org` |
| **Allow Insecure** | ❌ (выключено) |

### 6.3 Подключение
1. Выберите созданный сервер в списке
2. Нажмите **"Включить"**
3. Проверьте подключение


## ✅ 7. Проверка работы

### 7.1 На сервере
```bash
# Проверка статуса панели
sudo systemctl status s-ui

# Проверка открытых портов
sudo ss -tulpn | grep -E "443|2095|2096"

# Проверка логов
sudo journalctl -u s-ui -n 20 --no-pager
```

### 7.2 На клиенте
1. Проверьте IP: [ip.me](http://ip.me) - должен быть IP сервера
2. Проверьте скорость: [speedtest.net](https://speedtest.net)
3. Проверьте защиту: [whoer.net](https://whoer.net)

### 7.3 В панели S-UI
Перейдите в **"Dashboard"**:
- ✅ Трафик в реальном времени
- ✅ Подключенные клиенты
- ✅ Статистика по Inbound


## 📊 Итоговая конфигурация

| Компонент | Значение |
|-----------|----------|
| **Сервер** | Ubuntu (последняя версия) |
| **Пользователь** | `brakka` (с sudo правами) |
| **SSH** | Только по ключу, порт 22 |
| **Брандмауэр** | UFW активен |
| **Защита** | Fail2Ban настроен |
| **Домен** | `brk-france.duckdns.org` |
| **SSL** | Let's Encrypt (валидный) |
| **Панель** | S-UI v1.5.1 |
| **Порт панели** | `2095` (HTTPS) |
| **Порт подписки** | `2096` (HTTP) |
| **Протокол** | Hysteria2 |
| **Порт VPN** | `443` |


## 🔧 Полезные команды

### Управление S-UI
```bash
sudo systemctl restart s-ui
sudo systemctl status s-ui
sudo journalctl -u s-ui -f
```

### Управление Fail2Ban
```bash
sudo fail2ban-client status sshd
sudo fail2ban-client get sshd banip
sudo fail2ban-client set sshd unbanip IP_АДРЕС
```

### Управление UFW
```bash
sudo ufw status verbose
sudo ufw allow PORT/PROTOCOL
sudo ufw delete allow PORT/PROTOCOL
```

### Обновление сертификата
```bash
sudo certbot renew --dry-run
sudo systemctl restart s-ui
```


## ⚠️ Важные замечания

1. **Смена пароля admin** - обязательно смените пароль по умолчанию
2. **Резервное копирование** - сохраните копию `/etc/letsencrypt` и базы данных S-UI
3. **Автообновления** - настройте автоматическое обновление сертификата
4. **Мониторинг** - регулярно проверяйте логи и статус служб

