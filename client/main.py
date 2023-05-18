#!/usr/bin/env python3
import time
from client import Client
from pika_client import PikaClient
from gracefull_killer import GracefulKiller
import logging

RABBIT_HOST = "rabbit"


if __name__ == "__main__":
    # Wait 10 seconds to allow cluster to start
    time.sleep(10)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    pika = PikaClient(RABBIT_HOST)
    # Create queues and exchanges
    pika.declare_queue("CLIENT_queue")
    pika.declare_queue("CLIENT_results")
    client = Client(pika)
    gk = GracefulKiller(pika)
    try:
        client.run()
    except Exception as e:
        logging.exception(f"Exception in client: {e}")
