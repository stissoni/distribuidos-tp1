import logging
import signal
import sys
from filter import Filter
from pika_client import PikaClient
from gracefull_killer import GracefulKiller


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    pika = PikaClient("rabbit")
    stations_average_queue = pika.declare_queue("MONTREAL_stations_average")
    filter = Filter(pika)
    gc = GracefulKiller(pika)
    try:
        filter.run()
    except Exception as e:
        logging.error(f"Error consuming message: {e}")
