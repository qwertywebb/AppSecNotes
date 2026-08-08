# **Отчет по прохождению ColddBox: Easy**

**1. Первичная разведка (Recon)**

- Открытые порты: **80/tcp (Apache 2.4.18, WordPress 4.1.31)** и **4512/tcp (ssh)**.
- На вебе заинтересовала поисковая строка и возможность оставлять комментарий к посту (который проверяет модератор).

**2. Тестирование веб-уязвимостей**

- **XSS:** Попробовал оставить комментарии с xss-payload в обход фильтров — работает санитизация, XSS не катает.
- **SQLi:** Внедрил в поле comment `sleep(5)` — показалось, что сработало, но при дальнейших ручных тестах через параметры запросов (comment, author, email, url) результата не было. Все вводимые значения валидировались и санитизировались. SQLi не подтвердилась.
- **Проверка параметров (LFI):**
  - `http://IP/?s=` (ручная проверка, потом ffuf):
    `ffuf -w /usr/share/wordlists/LFI_DIRECTORIES.TXT -u "http://IP/?s=FUZZ" -fw 336`
  - Проверены другие параметры: `p`, `m`, `feed`, `cat`, `author` — ничего интересного.

**3. Перечисление директорий**

- `/wp-content` (Status: 200)
- `/wp-includes` (Status: 200)
- `/wp-admin` (Status: 200) — дефолтные креды не подошли.
- `/hidden` (Status: 200) — нашел сообщение: "U-R-G-E-N-T C0ldd, you changed Hugo's password, when you can send it to him... Philip". Это навело на мысль искать пароль для Hugo/C0ldd.

**4. Сканирование через Nuclei**

- Запустил: `nuclei -u IP`
- Нашел: `[CVE-2024-2473] [http] [medium] http://IP/wp-admin/?action=postpass`. Но практического применения не нашел.

**5. Брут SSH**

- Пользователи: C0ldd, Hugo, Philip
- Команда: `hydra -l C0ldd -P /usr/share/wordlists/rockyou.txt IP ssh -s 4512 -T200` — безрезультатно.

**6. WPScan и получение доступа в админку**

- `wpscan` подобрал креды: **`c0ldd:9876543210`**.

**7. Внедрение Reverse Shell**

- Залогинился в админку WordPress.
- В панели нашел email: `c0ldd@localhost.com`.
- Внедрил через редактор темы (файл 404.php) reverse shell.
- Получил шелл на сервере под пользователем `www-data`.

**8. Переключение на пользователя c0ldd**

- Флаг в `/home/c0ldd/user.txt`, но прав на чтение нет (`-rw-rw----`).
- В файле `wp-config.php` нашел креды подключения к БД:
  `define('DB_USER', 'c0ldd');`
  `define('DB_PASSWORD', 'cybersecurity');`
- Переключился на пользователя `c0ldd` (пароль `cybersecurity` подошел).
- Прочитал флаг: `RmVsaWNpZGFkZXMsIHBxxxxxxxxxxxxxxxxxxxxxxxxx==`. Это base64, декодировал — получил: **"Felicidades, primer nivel conseguido!"**

**9. Эскалация привилегий до root**

- Выполнил `sudo -l`:
  ```
  El usuario c0ldd puede ejecutar los siguientes comandos en ColddBox-Easy:
      (root) /usr/bin/vim
      (root) /bin/chmod
      (root) /usr/bin/ftp
  ```
- Использовал `vim` для создания интерактивной оболочки:
  `sudo /usr/bin/vim -c ':!/bin/sh' /dev/null`
- Получил root.
- Прочитал `root.txt`: `wqFGZWxpY2lkYWRlcywgbcOhcXVpbmEgxxxxxxxxxxxxxxx=` (декодируется как "¡Felicidades, máquina completada!").

**10. Итог и выводы**

- Основные этапы: поиск админ-кредов через wpscan → загрузка шелла через редактор темы → повышение до c0ldd через пароль из wp-config → эскалация до root через sudo на vim.
- **Главный вывод для себя:** если есть админский доступ к CMS, можно изменить шаблоны и добавить reverse shell. Это работает на многих CMS (WordPress, Joomla, Drupal и т.д.).
- **Полезный опыт:** впервые использовал wpscan, раньше не знал о нём — теперь буду применять чаще.
