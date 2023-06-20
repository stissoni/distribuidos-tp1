import sys
import socket
import docker

PROCESS_ID = int(sys.argv[1])


class Process:
    def __init__(self, id, host, port, container_id) -> None:
        if id is None:
            raise Exception("Processes must have an unique ID")
        self.id = id
        self.host = host
        self.port = port
        self.container_id = container_id

    def open_socket(self):
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_socket.settimeout(10)
        new_socket.connect((self.host, self.port))
        return new_socket

    def response_to_messages(self, s, replicas_service):
        while True:
            s.listen()
            conn, _ = s.accept()
            with conn:
                data = conn.recv(1024)
                if data == b"Election":
                    print(f"[REPLICA {PROCESS_ID}] Received ELECTION message")
                    response = b"OK"
                    conn.sendall(response)
                    replicas_service.start_election()
                elif data.startswith(b"Leader"):
                    print(f"[REPLICA {PROCESS_ID}] Received COORDINATOR message")
                    response = b"OK"
                    conn.sendall(response)
                    leader_id = int(data.split(b" ")[1])
                    replicas_service.set_new_leader(leader_id)
                elif data == b"Heartbeat":
                    print(f"[REPLICA {PROCESS_ID}] Received heartbeat")
                    response = b"Heartbeat"
                    conn.sendall(response)
                elif data == b"OK":
                    print(f"[REPLICA {PROCESS_ID}] Received OK message")
                conn.close()

    def restart_container(self):
        print(
            f"[REPLICA {PROCESS_ID}] Restarting process with ID: {self.process_id}, container ID: {self.container_id}"
        )
        client = docker.DockerClient(base_url="tcp://host.docker.internal:2375")
        container = client.containers.get(self.container_id)
        container.restart()

    def get_id(self):
        return self.id

    def is_alive(self):
        try:
            heartbeat_socket = self.open_socket()
            heartbeat_message = b"Heartbeat"
            heartbeat_socket.sendall(heartbeat_message)
            response = heartbeat_socket.recv(1024)
            print(
                f"[REPLICA {PROCESS_ID}] Received heartbeat response from process ID {self.id}"
            )
            heartbeat_socket.close()
            return response == heartbeat_message
        except Exception as e:
            print(f"[REPLICA {PROCESS_ID}] Error connecting to process {self.id}: {e}")
            return False
