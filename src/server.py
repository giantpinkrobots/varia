import socket
import time
import threading
import json

global myapp
varia_server_host = '127.0.0.1'
varia_server_port = 54682

def handle_connection(sock):
    while True:
        conn, _ = sock.accept()
        data = conn.recv(1024).decode()
        if data:
            data = json.loads(data)
            myapp.add_downloads(data)
        conn.close()
        time.sleep(0.5)

def start_varia_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((varia_server_host, varia_server_port))

    except OSError:
        return False # Another Varia instance is already running

    server.listen(1)
    threading.Thread(target=handle_connection, args=(server,), daemon=True).start()
    return True
   
def send_to_varia_instance(message):
    try:
        with socket.create_connection((varia_server_host, varia_server_port), timeout=2) as sock:
            sock.sendall(message.encode())

    except OSError:
        print("Couldn't contact existing instance.")