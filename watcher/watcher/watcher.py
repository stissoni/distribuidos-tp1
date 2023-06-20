import time


class Watcher:
    def __init__(self, processes_to_watch) -> None:
        self.processes_to_watch = processes_to_watch

    def watch(self):
        while True:
            for process in self.processes_to_watch:
                if not process.is_alive():
                    print(f"Process {process.get_id()} is not alive")
                    process.restart_container()
            time.sleep(5)
