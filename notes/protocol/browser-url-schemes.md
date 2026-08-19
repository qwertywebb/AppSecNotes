# Browser URL Schemes — протоколы и схемы URL

# Схема это параметр, который может быть обработан браузером.

## Основные схемы

| Scheme | Назначение |
|---|---|
| `http://` | HTTP-запрос к веб-серверу |
| `https://` | HTTP поверх TLS |
| `file://` | Доступ к локальному файлу в контексте клиента |
| `data:` | Данные непосредственно внутри URL |
| `ftp://` | FTP URL |
| `ws://` | WebSocket |
| `wss://` | WebSocket Secure |
| `mailto:` | Открытие почтового клиента |
| `tel:` | Телефонный номер |
| `javascript:` | JavaScript URL |

## Что важно для пентеста

### `data:`
Позволяет встроить данные непосредственно в URL:

```text
data:text/plain,Hello
data:text/html,<h1>Hello</h1>
data:text/html;base64,PGgxPkhlbGxvPC9oMT4=
```

Проверяется там, где приложение принимает пользовательский URL или HTML.

### `javascript:`
Может быть опасен в местах, где пользователь контролирует URL/`href`:

```html
<a href="javascript:alert(1)">Click</a>
```

### `file:`
Интересен прежде всего при серверной обработке URL. Если серверное приложение само умеет загружать URL, нужно отдельно проверять, поддерживает ли его URL parser `file:`.

### `Origin`
Для некоторых schemes браузер может использовать origin, который сериализуется как:

```text
Origin: null
```

Не следует считать `Origin: null` автоматически уязвимостью: безопасность CORS зависит от конкретной конфигурации приложения.

## Важное различие

```text
URL scheme ≠ transport protocol

https://
  └── URL scheme

HTTP
  └── application protocol

TCP
  └── transport protocol
```
