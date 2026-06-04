# POWERSHELL AD ENUMERATION — ПЕРЕЧИСЛЕНИЕ ЧЕРЕЗ POWERSHELL

## Два подхода

1. ActiveDirectory модуль (официальный от Microsoft)
2. PowerView (из PowerSploit, более мощный для пентеста)

---

# ЧАСТЬ 1: ACTIVE DIRECTORY МОДУЛЬ

## Загрузка модуля

# Проверить наличие
Get-Module -ListAvailable ActiveDirectory

# Импортировать
Import-Module ActiveDirectory

## User Enumeration

# Все пользователи
Get-ADUser -Filter *

# Конкретный пользователь с определенными свойствами
Get-ADUser -Identity Administrator -Properties LastLogonDate,MemberOf,Title,Description,PwdLastSet

# Поиск по фильтру (например, "admin" в имени)
Get-ADUser -Filter "Name -like '*admin*'"

Полезные свойства для пентеста:
- LastLogonDate — когда заходил (активен ли)
- MemberOf — группы пользователя
- Description — часто содержит пароли
- Title — должность
- PwdLastSet — когда менял пароль
- Enabled — активен ли аккаунт

## Group Enumeration

# Все группы
Get-ADGroup -Filter *

# Только имена групп
Get-ADGroup -Filter * | Select Name

# Участники группы
Get-ADGroupMember -Identity "Domain Admins"
Get-ADGroupMember -Identity "Remote Management Users"

## Computer Enumeration

# Все компьютеры
Get-ADComputer -Filter *

# Компьютеры с выбором полей
Get-ADComputer -Filter * | Select Name, OperatingSystem

## Password Policy

Get-ADDefaultDomainPasswordPolicy

Показывает:
- ComplexityEnabled — сложные пароли?
- MinPasswordLength — минимальная длина
- LockoutThreshold — попыток до блокировки
- LockoutDuration — длительность блокировки

---

# ЧАСТЬ 2: POWERVIEW (из PowerSploit)

## Что это

PowerView — PowerShell инструмент для глубокой enumeration AD.
Находится в PowerSploit/Recon/PowerView.ps1

## Загрузка PowerView

cd C:\Users\username\Downloads\PowerSploit-master\Recon
Import-Module .\PowerView.ps1

## User Enumeration

# Все пользователи
Get-DomainUser

# Пользователи с "admin" в имени
Get-DomainUser *admin*

# Пользователи с правами администратора
Get-DomainUser -AdminCount

# Пользователи с SPN (для Kerberoasting)
Get-DomainUser -SPN

## Group Enumeration

# Все группы
Get-DomainGroup

# Группы с "admin" в имени
Get-DomainGroup "*admin*"

# Участники группы
Get-DomainGroupMember -Identity "Domain Admins"

## Computer Enumeration

# Все компьютеры
Get-DomainComputer

## Преимущества PowerView перед ActiveDirectory модулем

- Больше функций для пентеста
- Работает без установки RSAT
- Может работать с доменом без полного присоединения
- Встроенные фильтры для поиска уязвимостей (SPN, AdminCount, и т.д.)

## Другие полезные команды PowerView

# Найти все доверительные отношения
Get-DomainTrust

# Найти все OU
Get-DomainOU

# Найти все GPO
Get-DomainGPO

# Найти компьютеры с уязвимыми настройками
Get-DomainComputer -Unconstrained

# Найти пользователей с пустым паролем
Get-DomainUser -Credential

---

# СРАВНЕНИЕ ИНСТРУМЕНТОВ

| Задача | NET команды | ActiveDirectory модуль | PowerView |
|--------|-------------|------------------------|-----------|
| Все пользователи | net user /domain | Get-ADUser -Filter * | Get-DomainUser |
| Все группы | net group /domain | Get-ADGroup -Filter * | Get-DomainGroup |
| Участники группы | net group "name" /domain | Get-ADGroupMember | Get-DomainGroupMember |
| Пользователи с админ правами | ❌ Нет | ❌ Нет (трудно) | Get-DomainUser -AdminCount |
| Пользователи с SPN | ❌ Нет | ❌ Нет (трудно) | Get-DomainUser -SPN |
| Компьютеры | net group "Domain Computers" /domain | Get-ADComputer -Filter * | Get-DomainComputer |

## Ключевой вывод

NET команды — базовый уровень (всегда доступны)
ActiveDirectory модуль — более информативный (требует RSAT)
PowerView — самый мощный для пентеста (специализированный)

---

# БЫСТРАЯ ШПАРГАЛКА (PowerShell)

# ActiveDirectory модуль
Import-Module ActiveDirectory
Get-ADUser -Identity username -Properties *
Get-ADGroupMember -Identity "Domain Admins"
Get-ADComputer -Filter * | Select Name
Get-ADDefaultDomainPasswordPolicy

# PowerView
Import-Module .\PowerView.ps1
Get-DomainUser
Get-DomainUser -SPN
Get-DomainUser -AdminCount
Get-DomainGroup "*admin*"
Get-DomainComputer
Get-DomainTrust


# ВАЖНОЕ ПРИМЕЧАНИЕ ПРО RSAT

RSAT (Remote Server Administration Tools) — это набор инструментов от Microsoft, который позволяет удаленно управлять серверами.

**Ключевой момент:** Модуль Active Directory для PowerShell (команды `Get-ADUser`, `Get-ADGroupMember` и т.д.) является частью RSAT 

Это означает:
1.  **На Domain Controller (DC):** Он работает из коробки, так как все нужные инструменты уже установлены.
2.  **На обычном компьютере (например, рабочей станции WRK):** Скорее всего, **не будет работать**. Ты получишь ошибку, что модуль не найден.
3.  **Чтобы это исправить:** Нужно доустановить RSAT. Это стандартная процедура для администраторов, но для пентестера это часто лишний шум и действия, которые могут быть замечены.

**Именно поэтому PowerView — это мощный инструмент:** Он **НЕ ТРЕБУЕТ установки RSAT**. Ты просто загружаешь один скрипт и начинаешь перечисление, что делает его идеальным для пентеста.