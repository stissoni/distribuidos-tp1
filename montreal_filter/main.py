import logging
import os
import socket
from filter import Filter
from pika_client import PikaClient
from gracefull_killer import GracefulKiller

ID_FILTER = os.getenv("ID_FILTER")

if __name__ == "__main__":
    if ID_FILTER is None:
        raise Exception("ID_FILTER environment variable not set")
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    pika = PikaClient("rabbit")
    # Get an unique ID for this replicated process, like the hostname
    address = socket.gethostname()
    stations_queue = pika.declare_queue(f"MONTREAL_stations_filter_{ID_FILTER}")
    trips_queue = pika.declare_queue("MONTREAL_montreal_trips")
    stations_average_queue = pika.declare_queue("MONTREAL_stations_average")
    gc = GracefulKiller(pika)
    filter = Filter(pika)
    try:
        filter.run(trips_queue, stations_queue)
    except Exception as e:
        logging.error(f"Error consuming message: {e}")
