#!/usr/bin/env python3
import signal
import sys
import time
from client import Client
from pika_client import PikaClient
import logging

RABBIT_HOST = "rabbit"

# 

class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        logging.info("action: receive_sigterm_signal | result: exiting gracefully!")
        self.pika.close()


if __name__ == "__main__":
    # Wait 10 seconds to allow cluster to start
    time.sleep(10)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    pika = PikaClient(RABBIT_HOST)
    # Create queues and exchanges
    pika.declare_queue("montreal_filter")
    pika.declare_queue("rainy_filter")
    pika.declare_queue("2016&2017_filter")
    pika.declare_exchange("weather", "fanout")
    pika.declare_exchange("stations", "fanout")
    client = Client(pika)
    gk = GracefulKiller()
    try:
        client.run()
    except Exception as e:
        logging.exception(f"Exception in client: {e}")
        sys.exit(0)
