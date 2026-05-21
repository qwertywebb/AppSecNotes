# cewl - парсит вебсайт и генерирует словарь паролей по ключевым фразам.
cewl -w list.txt -d 5 -m 5 http://thm.labs

# Crunch - генерирует список паролей по заданным опциям 
crunch 2 2 01234abcd -o crunch.txt

# CUPP - позволяет генерировать пароль, учитывая известные данные(др, кличка животного, работа)
python3 cupp.py -i

# RDPassSpray - утилита для эксплуатация password spray перебора usernames
python3 RDPassSpray.py -h

# SMB 
Tool: Metasploit (auxiliary/scanner//smb_login)