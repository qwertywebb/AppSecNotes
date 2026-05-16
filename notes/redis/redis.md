# Redis — Cheatsheet

## Подключение

```bash
# Подключение к серверу
redis-cli -h <IP> -p <PORT>

# С паролем
redis-cli -h <IP> -p <PORT> -a '<PASSWORD>'
```

## Аутентификация

```bash
# Внутри сессии
AUTH '<PASSWORD>'
```

## Основные команды

| Команда | Описание |
|---------|----------|
| `PING` | Проверить соединение (должен вернуть PONG) |
| `INFO` | Информация о сервере (версия, память, клиенты) |
| `KEYS *` | **Показать все ключи (опасно на проде!)** |
| `GET <key>` | Получить значение ключа |
| `SET <key> <value>` | Установить значение |
| `DEL <key>` | Удалить ключ |
| `TYPE <key>` | Узнать тип данных ключа |
| `EXISTS <key>` | Проверить существование ключа (1/0) |

## Работа с разными типами данных

### Строки (String)
```bash
SET user:1 "Alice"
GET user:1
```

### Хеши (Hash) — как объект/словарь
```bash
HSET user:2 name "Bob" age 30
HGET user:2 name
HGETALL user:2
```

### Списки (List)
```bash
LPUSH logs "error 1"
RPUSH logs "error 2"
LRANGE logs 0 -1
```

### Множества (Set)
```bash
SADD tags "redis"
SMEMBERS tags
```

## Сканирование (безопасная альтернатива KEYS *)
```bash
SCAN 0
SCAN 0 MATCH user:* COUNT 100
```

## Информация о сервере
```bash
INFO server      # версия, ОС
INFO clients     # количество подключений
INFO memory      # использование памяти
INFO stats       # статистика
CONFIG GET *     # получить все настройки (требует прав)
CONFIG GET requirepass  # проверка пароля
```

## Полезное для пентеста

| Задача | Команда |
|--------|---------|
| Проверить наличие пароля | `CONFIG GET requirepass` |
| Посмотреть версию | `INFO server` |
| Найти ключи с паролями | `KEYS *pass*` или `SCAN 0 MATCH *pass*` |
| Чтение конфигурации | `CONFIG GET *` |
| Сделать дамп всех ключей | `redis-cli --scan | while read key; do redis-cli GET "$key" >> dump.txt; done` |

## Выход
```bash
exit
quit
```

## Ошибки

| Ошибка | Решение |
|--------|---------|
| `NOAUTH Authentication required` | Выполнить `AUTH <пароль>` |
| `DENIED` | Недостаточно прав |
| `Connection refused` | Сервер не запущен или неверный порт |