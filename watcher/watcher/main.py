import time
import socket
import docker


# Function to check if a process is alive by sending a heartbeat message
def is_process_alive(process_id, heartbeat_socket):
    heartbeat_message = b"Heartbeat"
    try:
        print(f"[WATCHER 1] Sending heartbeat message to process ID {process_id}")
        heartbeat_socket.sendall(heartbeat_message)
        response = heartbeat_socket.recv(1024)
        print(f"[WATCHER 1] Received heartbeat response from process ID {process_id}")
        return response == heartbeat_message
    except Exception as e:
        raise Exception


# Function to start a process container in the host using Docker SDK
def start_process(process_id, container_id):
    print(
        f"[WATCHER 1] Restarting process with ID: {process_id}, container ID: {container_id}"
    )

    client = docker.DockerClient(base_url="tcp://host.docker.internal:2375")
    container = client.containers.get(container_id)
    container.restart()

    print(f"[WATCHER 1] Started container ID: {container.id}")


processes = {
    1: {
        "name": "test_process_1",
        "port": 5001,
        "container_id": "watcher-test_process_1-1",
    },
    2: {
        "name": "test_process_2",
        "port": 5002,
        "container_id": "watcher-test_process_2-1",
    },
}


# Main loop to check the heartbeat
while True:
    for process in processes.keys():
        process_id = process
        address = (processes[process]["name"], processes[process]["port"])
        container_id = processes[process]["container_id"]

        print(f"[WATCHER 1] Checking process {process_id} in address {address}")

        process_running = False
        try:
            heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            heartbeat_socket.connect(address)
            process_running = is_process_alive(process_id, heartbeat_socket)
            heartbeat_socket.close()
            process_running = True
        except Exception as e:
            print(f"[WATCHER 1] Error connecting to process {process_id}: {e}")
            process_running = False

        if not process_running:
            start_process(process_id, container_id)

    time.sleep(5)
