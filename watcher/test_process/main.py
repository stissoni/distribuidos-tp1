import os
import socket

id = os.getenv("ID")

print(f"[TEST PROCESS {id}] Starting process with ID: {id}...")

HOST = "0.0.0.0"
PORT = 5000 + int(id)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print(f"[TEST PROCESS {id}] Socket created")

s.bind((HOST, PORT))

print(f"[TEST PROCESS {id}] Socket binded to", (HOST, PORT))

while True:
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"[TEST PROCESS {id}] Connected by", addr)
        # Iterate over received messages
        while True:
            data = conn.recv(1024)
            if not data:
                break
            response = b"Heartbeat"
            conn.sendall(response)
