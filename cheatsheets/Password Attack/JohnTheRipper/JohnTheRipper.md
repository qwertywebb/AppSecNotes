# ssh:
ssh2john id_rsa > id_rsa.hash
john --wordlist=/usr/share/wordlists/rockyou.txt id_rsa.hash

# gpg:
gpg2john private.gpg > private.hash

# archive:
zip2john archive.zip > archive.hash
john --wordlist=/usr/share/wordlists/rockyou.txt archive.hash

password:

# Копируем нужные файлы (требуются root права через любую утилиту nano и тд), главное чтобы был доступ к /etc/shadow
sudo cp /etc/passwd /tmp/passwd.txt
sudo cp /etc/shadow /tmp/shadow.txt

# Сделаем unshadow

unshadow /tmp/passwd.txt /tmp/shadow.txt > /tmp/passwords.txt

# Используем John the Ripper для взлома паролей

john --wordlist=/usr/share/wordlists/rockyou.txt /tmp/passwords.txt


# Hash:
john --wordlist=./easypeasy_1596838725703.txt hash.txt

# Если знаем формат:
john --format=Raw-SHA256 --wordlist=./easypeasy_1596838725703.txt hash.txt


# РАБОТА С ПРАВИЛАМИ
1. В /etc/john/john.conf
добавляем правило, если знаем по какому принципу создаются пароли
Например для [symbol][word][0-9][0-9]:
[List.Rules:Test-rules]
^[!@#$%%&*()_-+] Az"[0-9][0-9]"
2. Создаем новый словарь из другого словаря, применяя правила
john --wordlist=rockyou.txt --rules=Test-rules --stdout > new_wordlist.txt

