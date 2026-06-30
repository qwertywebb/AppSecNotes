# CSP (Content Security Policy) — Шпаргалка

## Что это

CSP — механизм безопасности, который сообщает браузеру, откуда разрешено загружать ресурсы (скрипты, стили, изображения и т.д.). Защищает от XSS, data injection и других атак.

## Формат заголовка

```
Content-Security-Policy: directive1 value1; directive2 value2
```


## Основные директивы

| Директива | Назначение |
|-----------|------------|
| `default-src` | Источник по умолчанию для всех ресурсов |
| `script-src` | Откуда можно загружать скрипты |
| `style-src` | Откуда можно загружать стили |
| `img-src` | Откуда можно загружать картинки |
| `connect-src` | Откуда можно делать fetch/XHR запросы |
| `font-src` | Откуда можно загружать шрифты |
| `frame-src` | Откуда можно загружать iframe |
| `object-src` | Откуда можно загружать плагины (Flash, Java) |
| `base-uri` | Какие URL разрешены в теге `<base>` |
| `form-action` | Куда можно отправлять формы |
| `frame-ancestors` | Кто может встраивать страницу в iframe |
| `report-uri` | Куда отправлять отчёты о нарушениях |


## Значения для директив

| Значение | Описание |
|----------|----------|
| `'self'` | Только свой домен |
| `'none'` | Запретить всё |
| `'unsafe-inline'` | Разрешить inline-код (опасно!) |
| `'unsafe-eval'` | Разрешить `eval()` (опасно!) |
| `'strict-dynamic'` | Доверять цепочке загрузки |
| `https://cdn.com` | Конкретный домен |
| `*` | Любой источник (опасно) |
| `data:` | Разрешить data: URI |
| `http://*.site.com` | Любой поддомен |
| `'nonce-abc123'` | Одноразовый токен для inline-скриптов |
| `'sha256-abc'` | Хеш inline-кода |


## Примеры политик

### Минимальная безопасная политика

```
default-src 'self'; object-src 'none'
```

### С внешними ресурсами

```
default-src 'self'; script-src 'self' https://cdn.com; style-src 'self'
```

### Разрешить inline-стили, запретить inline-скрипты
```
script-src 'self'; style-src 'self' 'unsafe-inline'
```

### С nonce (безопасные inline-скрипты)


```
script-src 'nonce-r4nd0m' 'strict-dynamic'
```

В HTML:
```html
<script nonce="r4nd0m">alert(1)</script>
```

### С report-uri (логирование нарушений)

```
default-src 'self'; report-uri /csp-violation
```

### Защита от clickjacking (вместо X-Frame-Options)

```
frame-ancestors 'self' https://trusted.com
```


## Что нельзя делать и почему

| Ошибка | Почему опасно |
|--------|---------------|
| `script-src 'unsafe-inline'` | XSS через inline-код |
| `script-src 'unsafe-eval'` | `eval()` обходит политику |
| `default-src *` | Любой сайт может загружать ресурсы |
| `object-src 'self'` | Flash/Java могут быть векторами атак |


## Быстрая шпаргалка

```bash
# Проверить CSP в ответе
curl -I https://example.com | grep -i csp

# Посмотреть в браузере
# DevTools → Network → заголовки ответа

# Обойти CSP (если слабая политика)
# 1. Использовать JSONP-колбэк на доверенном домене
# 2. Использовать загрузку через iframe
# 3. Использовать redirect с параметром
```


## Защита от CSP-обхода

- `'unsafe-inline'` — **всегда выключать**
- `'unsafe-eval'` — **выключать**
- `*` — **запрещать**
- Использовать `nonce` для динамических скриптов
- Использовать `strict-dynamic` для современных приложений
- Настроить `report-uri` для мониторинга нарушений