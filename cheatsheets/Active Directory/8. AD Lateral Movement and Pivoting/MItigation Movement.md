# ЗАЩИТА ОТ LATERAL MOVEMENT

## LAPS (Local Administrator Password Solution)

**Проблема:** Одинаковый пароль локального администратора на всех компьютерах.

**Решение:** Windows LAPS (встроен в Windows 11 22H2+, Server 2022+). Каждый компьютер получает уникальный случайный пароль для локального Administrator. Пароль хранится в AD, автоматически ротируется.

**Что останавливает:** Pass-the-Hash с локальным админским хэшем. Хэш с одного компьютера не подходит для других.


## Ограничение прав локального администратора

**Проблема:** PsExec, WMI, DCOM, SMBExec требуют локального админа на цели.

**Решение:** Обычные пользователи — не локальные админы на других машинах.

**Tier модель:**
- Tier 0 (Domain Admins) → только на DC
- Tier 1 (Server Admins) → только на серверы
- Tier 2 (Workstation Admins) → только на рабочие станции

**Что останавливает:** PsExec, WMI, DCOM, SMBExec.


## SMB Signing

**Проблема:** Relay атаки и некоторые SMB методы выполнения.

**Решение:** Включить через GPO:
- Microsoft network server: Digitally sign communications (always) → Enabled
- Microsoft network client: Digitally sign communications (always) → Enabled

**Что останавливает:** NTLM Relay, усложняет SMB методы.

---

## Ограничение NTLM

**Проблема:** Pass-the-Hash работает через NTLM.

**Решение:** GPO → Network Security → Restrict NTLM → Deny All (Kerberos-only). Credential Guard изолирует LSASS.

**Что останавливает:** Pass-the-Hash, дамп LSASS.


## Хостовые файрволы

**Проблема:** Прямой доступ к административным портам (445 SMB, 5985 WinRM, 3389 RDP).

**Решение:** Блокировать входящие подключения на эти порты между рабочими станциями через GPO.

**Что останавливает:** PsExec, WinRM, RDP между рабочими станциями.


## Сетевая сегментация

**Проблема:** Pivot хост имеет доступ ко всем подсетям.

**Решение:** Workstations, Servers, DC в разных VLAN. Firewall правила между ними. DC — без интернета.

**Что останавливает:** Pivoting между подсетями.


## PAWs (Privileged Access Workstations)

**Проблема:** Domain Admin логинится на обычные машины → хэш крадется.

**Решение:** Отдельная защищенная машина только для Tier 0 задач. Повседневная работа — на другой машине.

**Что останавливает:** Кража DA кредов с обычных машин (их там просто нет).


## Мониторинг и детекция

| Event ID | Что алертить |
|----------|--------------|
| 4624 Type 3 | Workstation логинится на другую workstation |
| 4624 Type 10 | Domain Admin RDP на workstation |
| 4648 | Explicit credential use (PsExec, runas) |
| 7045 | Новая служба с коротким рандомным именем (PsExec) |
| 4698 | Scheduled task created (AtExec) |
| 4688 | Process creation (требует аудит командной строки) |
