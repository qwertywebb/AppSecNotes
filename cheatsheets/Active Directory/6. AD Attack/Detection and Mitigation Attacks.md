# ОБНАРУЖЕНИЕ АТАК ЧЕРЕЗ WINDOWS EVENT LOGS

Атаки на аутентификацию оставляют следы в логах Windows.
Умение читать эти логи = умение не попадаться (для атакующего) или обнаруживать атаки (для защитника).

## Основные Event ID для аутентификации

Event ID 4624 — успешный вход (Security log)
- Смотреть на: Authentication Package (NTLM или Kerberos)
- Смотреть на: Logon Type
  * Type 3 = сетевой вход (SMB, WinRM, Pass-the-Hash)
  * Type 10 = удаленный интерактивный (RDP)
- Смотреть на: Source Network Address (при NTLM часто пустой — плохо для расследования)

Event ID 4625 — неудачный вход
- Используется для обнаружения password spraying (много неудач под разные учетки)

Event ID 4768 — запрос TGT (Kerberos)

Event ID 4769 — запрос TGS (сервисного билета)
- Ключевой для обнаружения Kerberoasting
- Смотреть на: Ticket Encryption Type
  * 0x17 = RC4-HMAC (подозрительно, используется для взлома)
  * 0x12 = AES-256 (нормально для современных систем)

Event ID 4771 — предварительная аутентификация Kerberos не удалась
- Используется для обнаружения AS-REP Roasting
- Также показывает brute-force атаки

## Как детектить конкретные атаки

Pass-the-Hash:
- Искать Event ID 4624 с Authentication Package = NTLM и Logon Type = 3
- Атака на DC через NTLM — почти всегда красный флаг
- Проблема для защитника: Source Network Address часто пустой

Kerberoasting:
- Резкий всплеск Event ID 4769 от одного пользователя
- Ticket Encryption Type = 0x17 (RC4) вместо AES-256 (0x12)
- Атакующий может специально запрашивать RC4 чтобы быстрее взломать

AS-REP Roasting / Password Spray:
- Всплеск Event ID 4771 по многим учеткам

# МИТИГАЦИИ (ЗАЩИТА)

Pass-the-Hash:
- Добавить привилегированные учетки в группу Protected Users
- Отключать NTLM везде, где можно использовать Kerberos

NTLM Relay:
- Включить подпись SMB (SMB Signing)
- Extended Protection for Authentication (EPA) для HTTP и Exchange

Kerberoasting:
- Длинные случайные пароли для сервисных учеток (30+ символов)
- Использовать gMSA (Group Managed Service Accounts) — пароли ротируются автоматически

Golden Ticket:
- Защищать учетку KRBTGT (мониторить доступ)
- После подозрения на компрометацию — сменить пароль KRBTGT ДВАЖДЫ

Password Spray:
- Настроить политику блокировки после N неудачных попыток
- Мониторить Event ID 4625

# Для пентестера (как не попасться)

- Используй Kerberos вместо NTLM где возможно — NTLM оставляет меньше IP в логах
- Работай через jump-серверы, чтобы запутать источник
- Очищай логи или обходи их
- Используй AES-256 запросы вместо RC4 при Kerberoasting (если можно)

# КЛЮЧЕВЫЕ ВЫВОДЫ ПО ЛОГАМ И ЗАЩИТЕ

1. NTLM логи имеют пустой Source IP — сложнее расследование.
2. Kerberos логи (4768, 4769) содержат IP атакующего.
3. RC4 запросы TGS — красный флаг (Kerberoasting).
4. Защита от Kerberoasting: длинные пароли или ротация.
5. От Golden Ticket: менять пароль KRBTGT ДВАЖДЫ.
6. От Password Spray: политика блокировки после N неудач.
7. От NTLM Relay: SMB Signing и EPA.
8. От Pass-the-Hash: Protected Users группа и отключение NTLM.