# Отчет по прохождению Ninja Skills

## 1. Цель работы

Исследовать файловую систему и ответить на вопросы о файлах, разбросанных по различным директориям.

## 2. Список файлов для анализа

8V2L, bny0, c4ZX, D8B3, FHl1, oiMO, PFbD, rmfX, SRSq, uqyw, v2Vb, X1Uy

## 3. Поиск местоположения файлов

Впервые использовал команду `find` для поиска большого количества файлов сразу через `-o`.

find / -type f -name D8B3 -o -name FHl1 -o -name oiMO -o -name PFbD -o -name rmfX -o -name SRSq -o -name uqyw -o -name v2Vb -o -name X1Uy -o -name c4ZX -o -name bny0 -o -name 8V2L 2>/dev/null

**Результат:**
/mnt/D8B3
/mnt/c4ZX
/var/FHl1
/var/log/uqyw
/opt/PFbD
/opt/oiMO
/media/rmfX
/etc/8V2L
/etc/ssh/SRSq
/home/v2Vb
/X1Uy

## 4. Определение владельца best-group

ls -la /mnt/D8B3 /mnt/c4ZX /var/FHl1 /var/log/uqyw /opt/PFbD /opt/oiMO /media/rmfX /etc/8V2L /etc/ssh/SRSq /home/v2Vb /X1Uy

**Результат:**
-rwxrwxr-x 1 new-user new-user 13545 Oct 23 2019 /etc/8V2L
-rw-rw-r-- 1 new-user new-user 13545 Oct 23 2019 /etc/ssh/SRSq
-rw-rw-r-- 1 new-user best-group 13545 Oct 23 2019 /home/v2Vb
-rw-rw-r-- 1 new-user new-user 13545 Oct 23 2019 /media/rmfX
-rw-rw-r-- 1 new-user new-user 13545 Oct 23 2019 /mnt/c4ZX
-rw-rw-r-- 1 new-user best-group 13545 Oct 23 2019 /mnt/D8B3
-rw-rw-r-- 1 new-user new-user 13545 Oct 23 2019 /opt/oiMO
-rw-rw-r-- 1 new-user new-user 13545 Oct 23 2019 /opt/PFbD
-rw-rw-r-- 1 new-user new-user 13545 Oct 23 2019 /var/FHl1
-rw-rw-r-- 1 new-user new-user 13545 Oct 23 2019 /var/log/uqyw
-rw-rw-r-- 1 newer-user new-user 13545 Oct 23 2019 /X1Uy

Файлы, принадлежащие группе `best-group`: **D8B3 v2Vb** (в алфавитном порядке)

## 5. Поиск IP-адреса в файлах

cat /opt/oiMO

В выводе найден IP-адрес:
...1.1.1.1VeiSLv...

**Ответ:** `/opt/oiMO`

## 6. Поиск файла по SHA1-хешу

for file in /mnt/D8B3 /mnt/c4ZX /var/FHl1 /var/log/uqyw /opt/PFbD /opt/oiMO /media/rmfX /etc/8V2L /etc/ssh/SRSq /home/v2Vb /X1Uy; do
sha1sum "$file" 2>/dev/null
done

**Результат:**
2c8de970ff0701c8fd6c55db8a5315e5615a9575 /mnt/D8B3
9d54da7584015647ba052173b84d45e8007eba94 /mnt/c4ZX
d5a35473a856ea30bfec5bf67b8b6e1fe96475b3 /var/FHl1
57226b5f4f1d5ca128f606581d7ca9bd6c45ca13 /var/log/uqyw
256933c34f1b42522298282ce5df3642be9a2dc9 /opt/PFbD
5b34294b3caa59c1006854fa0901352bf6476a8c /opt/oiMO
4ef4c2df08bc60139c29e222f537b6bea7e4d6fa /media/rmfX
0323e62f06b29ddbbe18f30a89cc123ae479a346 /etc/8V2L
acbbbce6c56feb7e351f866b806427403b7b103d /etc/ssh/SRSq
7324353e3cd047b8150e0c95edf12e28be7c55d3 /home/v2Vb
59840c46fb64a4faeabb37da0744a46967d87e57 /X1Uy

Хеш `9d54da7584015647ba052173b84d45e8007eba94` принадлежит файлу **c4ZX**

## 7. Подсчёт строк в файлах

Узнал команду `wc -l` для подсчета количества строк в файлах.

wc -l /mnt/D8B3 /mnt/c4ZX /var/FHl1 /var/log/uqyw /opt/PFbD /opt/oiMO /media/rmfX /etc/8V2L /etc/ssh/SRSq /home/v2Vb /X1Uy

**Результат:** файл `bny0` содержит 230 строк.

**Ответ:** `bny0`

## 8. Определение владельца с UID 502

ls -la /X1Uy

**Результат:**
-rw-rw-r-- 1 newer-user new-user 13545 Oct 23 2019 /X1Uy

id newer-user

**Результат:**
uid=502(newer-user) gid=503(newer-user) groups=503(newer-user)

**Ответ:** `X1Uy`

## 9. Поиск исполняемого файла для всех

ls -la /etc/8V2L

**Результат:**
-rwxrwxr-x 1 new-user new-user 13545 Oct 23 2019 /etc/8V2L

Права `-rwxrwxr-x` означают, что файл исполняемый для всех.

**Ответ:** `/etc/8V2L`

## 10. Новые навыки

- Впервые использовал `find` с несколькими `-o` для поиска большого количества файлов одновременно
- Узнал команду `wc -l` для подсчета строк в файлах
