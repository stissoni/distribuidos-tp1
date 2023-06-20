import sys
import time


PROCESS_ID = int(sys.argv[1])


class ReplicasService:
    def __init__(self):
        self.replicated_procesess = []
        self.leader = None
        self.my_process = None

    def set_my_process(self, process):
        self.add_process(process)
        self.my_process = process

    def get_my_process(self):
        return self.my_process

    def is_leader(self, process):
        process_id = process.get_id()
        try:
            leader_id = self.leader.get_id()
        except Exception as e:
            print(
                f"Could not found leader ID. Probably there is no leader yet. Error: {e}"
            )
            return False
        return process_id == leader_id

    def get_process(self, process_id):
        for replicated_process in self.replicated_procesess:
            if replicated_process.get_id() == process_id:
                return replicated_process

    def add_process(self, process):
        self.replicated_procesess.append(process)

    def set_new_leader(self, leader_id):
        new_leader = self.get_process(leader_id)
        self.leader = new_leader
        print(f"[REPLICA {PROCESS_ID}] New leader is {leader_id}")

    def get_leader(self):
        return self.leader

    def broadcast_new_leader(self):
        for process in self.replicated_procesess:
            if process == self.my_process:
                continue
            else:
                process.send_coordinator_message(self.leader.get_id())

    def start_election(self):
        there_is_new_leader = False
        for process in self.replicated_procesess:
            if process.get_id() > PROCESS_ID:
                there_is_new_leader = process.send_election_message()
            if there_is_new_leader:
                break
        if there_is_new_leader:
            print(f"[REPLICA {PROCESS_ID}] There is a new leader!")
            time.sleep(5)
        else:
            print(f"[REPLICA {PROCESS_ID}] I'm the new leader!")
            my_id = self.get_my_process().get_id()
            self.set_new_leader(my_id)
            self.broadcast_new_leader()
