import socket
import sys
import time

from threading import Thread
from replicas_service import ReplicasService
from watcher_replicated_process import WatcherReplicatedProcess

PROCESS_ID = int(sys.argv[1])


# List of processes with their IDs and ports
processes = {1: 8001, 2: 8002, 3: 8003}

replicas_service = ReplicasService()
for process_id in processes.keys():
    replicated_process = WatcherReplicatedProcess(
        process_id, "localhost", processes[process_id]
    )
    if process_id == PROCESS_ID:
        replicas_service.set_my_process(replicated_process)
    else:
        replicas_service.add_process(replicated_process)


# Create TCP socket
print(f"[REPLICA {PROCESS_ID}] Listening on port {processes[PROCESS_ID]}")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("0.0.0.0", processes[PROCESS_ID]))


# Start a thread to responde to messages
print(f"[REPLICA {PROCESS_ID}] Starting thread to respond messages...")
my_process = replicas_service.my_process
handler = Thread(
    target=my_process.response_to_messages, args=(s, replicas_service), daemon=True
)
handler.start()

# Start election to choose the leader
replicas_service.start_election()


# Main loop
while True:
    is_alive = True
    if replicas_service.get_leader() is None:
        print(f"[REPLICA {PROCESS_ID}] Leader not determined yet! Wating...")
    elif replicas_service.is_leader(replicas_service.get_my_process()):
        # Watch the proceses and restart them if they are not alive
        print("Doing some leader stuff")
    else:
        is_alive = replicas_service.get_leader().is_alive()

    if not is_alive:
        replicas_service.start_election()

    time.sleep(5)
