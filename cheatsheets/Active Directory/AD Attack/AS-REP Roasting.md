# AS-REP ROASTING — АТАКА НА УЧЕТКИ БЕЗ PRE-AUTHENTICATION(не нужна учетка)

## Что это

Атака на пользователей, у которых отключена предварительная аутентификация Kerberos (флаг UF_DONT_REQUIRE_PREAUTH).

Когда pre-authentication отключена, KDC отправляет AS-REP (зашифрованную часть TGT) любому, кто запросит, без проверки пароля.

Эту AS-REP можно перехватить и взломать офлайн.

## Отличие от Kerberoasting

| Аспект | Kerberoasting | AS-REP Roasting |
|--------|---------------|-----------------|
| Цель | Service accounts (с SPN) | Любые пользователи |
| Требования | SPN у учетки | UF_DONT_REQUIRE_PREAUTH |
| Аутентификация | Нужен любой доменный пользователь | НЕ нужна учетка вообще |

## Почему это работает

Нормальный процесс Kerberos:
1. Клиент отправляет AS-REQ (username + timestamp, зашифрованный хэшом пароля)
2. KDC расшифровывает, проверяет → выдает TGT

Если pre-authentication ОТКЛЮЧЕНА:
1. KDC НЕ проверяет пароль
2. KDC сразу отправляет AS-REP (TGT, зашифрованный хэшом пользователя)
3. Атакующий перехватывает и взламывает офлайн

---

# ЭТАП 1: НАЙТИ УЧЕТКИ С UF_DONT_REQUIRE_PREAUTH

## Инструменты

### GetNPUsers.py (Impacket) — Linux

GetNPUsers.py DOMAIN/ -dc-ip DC_IP -usersfile users.txt -format hashcat -outputfile hashes.txt -no-pass

Параметры:
- -usersfile — файл со списком пользователей
- -format hashcat — формат для Hashcat (режим 18200)
- -outputfile — куда сохранить хэши
- -no-pass — без пароля (анонимно)

### Rubeus — Windows (если есть доступ к Windows машине)

Rubeus.exe asreproast

Автоматически находит всех пользователей с отключенной pre-auth.

---

# ЭТАП 2: ВЗЛОМ AS-REP ХЭША

## Hashcat режим 18200

hashcat -m 18200 hashes.txt /usr/share/wordlists/rockyou.txt

-m 18200 — AS-REP хэши

## Формат хэша

$krb5asrep$23$username@DOMAIN:hash

Пример: $krb5asrep$23$asrepuser1@TRYHACKME.LOC:32015b1273c454cb721c60d716e37751$3a325977...

---

# КЛЮЧЕВЫЕ ОСОБЕННОСТИ

- Не требует аутентификации (атакует анонимно)
- Не генерирует много шума (в отличие от спрея)
- Цель — любые учетки, не только сервисные
- Успех зависит от силы пароля

---

# МИТИГАЦИИ

1. Включить pre-authentication для ВСЕХ пользователей
2. Длинные сложные пароли
3. Мониторинг аномальных AS-REP запросов (Event ID 4768)

---

# БЫСТРАЯ ШПАРГАЛКА

# Найти уязвимые учетки (Linux)
GetNPUsers.py DOMAIN/ -dc-ip DC_IP -usersfile users.txt -format hashcat -outputfile asrephashes.txt -no-pass

# Взломать хэши
hashcat -m 18200 asrephashes.txt /usr/share/wordlists/rockyou.txt

# Найти уязвимые учетки (Windows)
Rubeus.exe asreproast /format:hashcat /outfile:asrephashes.txt