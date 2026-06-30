---TAR---
# Создать tar.gz архив
tar czf archive.tar.gz ./file

# Распаковать tar.gz
tar xzf archive.tar.gz

# Распаковать с удалением двух уровней папок
tar xzf ../firefox.tar.gz --strip-components=2

---GZIP---
# Сжать файл
gzip file.txt

# Сжать с сохранением исходного
gzip -c file.txt > file.txt.gz

# Распаковать
gunzip file.txt.gz


---ZIP/RAR---
# Распаковать ZIP
unzip archive.zip

# Распаковать RAR/7z/ISO
unar archive.rar