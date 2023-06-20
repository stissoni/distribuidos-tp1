import sys

from process import Process

PROCESS_ID = int(sys.argv[1])


class WatcherReplicatedProcess(Process):
    def __init__(self, id, host, port) -> None:
        super().__init__(id, host, port, None)

    def send_coordinator_message(self, new_coordinator_id):
        print(
            f"[REPLICA {PROCESS_ID}] Sending COORDINATOR message to process ID {self.id}"
        )
        try:
            leader_socket = self.open_socket()
            leader_message = f"Leader {new_coordinator_id}".encode()
            leader_socket.sendall(leader_message)
            response = leader_socket.recv(1024)
            if response == b"OK":
                print(
                    f"[REPLICA {PROCESS_ID}] Received OK for COORDINATOR from {self.id}"
                )
            leader_socket.close()
        except Exception as e:
            print(
                f"[REPLICA {PROCESS_ID}] Error sending COORDINATOR message to {self.id}: {e}"
            )

    def send_election_message(self):
        print(
            f"[REPLICA {PROCESS_ID}] Sending ELECTION message to process ID {self.id}"
        )
        there_is_new_leader = False
        try:
            election_socket = self.open_socket()
            election_message = b"Election"
            election_socket.sendall(election_message)
            response = election_socket.recv(1024)
            if response == b"OK":
                print(
                    f"[REPLICA {PROCESS_ID}] Received OK for ELECTION response from {self.id}"
                )
                there_is_new_leader = True
            election_socket.close()
        except Exception as e:
            print(
                f"[REPLICA {PROCESS_ID}] Error sending ELECTION message to {self.id}: {e}"
            )
        return there_is_new_leader
