import socket
import sys
from threading import Thread
import time

PROCESS_ID = int(sys.argv[1])


def is_process_alive(process_id, heartbeat_socket):
    heartbeat_message = b"Heartbeat"
    print(
        f"[REPLICA {PROCESS_ID}] Sending heartbeat message to process ID {process_id}"
    )
    heartbeat_socket.sendall(heartbeat_message)
    response = heartbeat_socket.recv(1024)
    print(
        f"[REPLICA {PROCESS_ID}] Received heartbeat response from process ID {process_id}"
    )
    return response == heartbeat_message


def broadcast_leader_message():
    for process_id in processes_keys:
        if process_id != PROCESS_ID:
            try:
                leader_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                leader_socket.settimeout(10)
                leader_socket.connect(("localhost", processes[process_id]))
                print(
                    f"[REPLICA {PROCESS_ID}] Sending leader message to process ID {process_id}"
                )
                leader_socket.sendall(f"Leader {PROCESS_ID}".encode())
                response = leader_socket.recv(1024)
                print(
                    f"[REPLICA {PROCESS_ID}] Received leader response from process ID {process_id}"
                )
                if response == b"OK":
                    print(f"[REPLICA {PROCESS_ID}] Received OK from {process_id}")
                leader_socket.close()
            except Exception as e:
                print(f"[REPLICA {PROCESS_ID}] Error sending leader message: {e}")
                continue


def start_election():
    there_is_new_leader = False
    for process_id in processes_keys:
        if process_id > PROCESS_ID:
            try:
                election_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                election_socket.settimeout(10)
                election_socket.connect(("localhost", processes[process_id]))
                print(
                    f"[REPLICA {PROCESS_ID}] Sending ELECTION message to process ID {process_id}"
                )
                election_socket.sendall(b"Election")
                response = election_socket.recv(1024)
                if response == b"OK":
                    print(
                        f"[REPLICA {PROCESS_ID}] Received OK for ELECTION response from process ID {process_id}"
                    )
                    there_is_new_leader = True
                election_socket.close()
            except Exception as e:
                print(f"[REPLICA {PROCESS_ID}] Error sending ELECTION message: {e}")
                continue
    if there_is_new_leader:
        print(f"[REPLICA {PROCESS_ID}] There is a new leader!")
        # Wait for the coordinator message
        time.sleep(5)
        return
    else:
        print(f"[REPLICA {PROCESS_ID}] I'm the new leader!")
        global i_lead
        i_lead = True
        broadcast_leader_message()
        return


def response_to_messages(s):
    while True:
        s.listen()
        conn, _ = s.accept()
        with conn:
            data = conn.recv(1024)
            if data == b"Election":
                print(f"[REPLICA {PROCESS_ID}] Received ELECTION message")
                response = b"OK"
                conn.sendall(response)
                start_election()
            elif data.startswith(b"Leader"):
                print(f"[REPLICA {PROCESS_ID}] Received LEADER message")
                response = b"OK"
                conn.sendall(response)
                global LEADER_ID
                global i_lead
                LEADER_ID = int(data.split(b" ")[1])
                i_lead = False
                print(f"[REPLICA {PROCESS_ID}] New leader is {LEADER_ID}")
            elif data == b"Heartbeat":
                print(f"[REPLICA {PROCESS_ID}] Received Heartbeat")
                response = b"Heartbeat"
                conn.sendall(response)
            elif data == b"OK":
                print(f"[REPLICA {PROCESS_ID}] Received OK")
            conn.close()


# List of processes with their IDs and ports
processes = {1: 8001, 2: 8002, 3: 8003}

# Get the processes keys as a list and sort it
processes_keys = list(processes.keys())
processes_keys.sort()
LEADER_ID = None
i_lead = False

# Create TCP socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
my_port = processes[PROCESS_ID]
print(f"[REPLICA {PROCESS_ID}] Listening on port {my_port}")
s.bind(("0.0.0.0", my_port))

# Start a thread to responde to heartbeats
print(f"[REPLICA {PROCESS_ID}] Starting thread to respond to heartbeats...")
handler = Thread(target=response_to_messages, args=(s,))
handler.daemon = True
handler.start()

# Grace period for everyone to start
print(f"[REPLICA {PROCESS_ID}] Waiting {15} s for everyone to start...")
time.sleep(15)

# Start election to choose the leader
start_election()

while True:
    # Connect to other processes
    if i_lead:
        # Doing some leader stuff
        print(f"[REPLICA {PROCESS_ID}] Doing some leader stuff!")
        time.sleep(5)
        continue
    try:
        heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        heartbeat_socket.settimeout(10)
        heartbeat_socket.connect(("localhost", processes[LEADER_ID]))
        is_alive = is_process_alive(LEADER_ID, heartbeat_socket)
        heartbeat_socket.close()
    except Exception as e:
        print(f"[REPLICA {PROCESS_ID}] Error connecting to process {LEADER_ID}: {e}")
        is_alive = False

    if not is_alive:
        start_election()

    time.sleep(5)
