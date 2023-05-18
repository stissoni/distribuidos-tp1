import logging
import sys
from filter import Filter
from pika_client import PikaClient
from gracefull_killer import GracefulKiller

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    pika = PikaClient("rabbit")
    stations_queue = pika.bind_to_exchange("stations")
    trips_queue = pika.declare_queue("MONTREAL_montreal_trips")
    stations_average_queue = pika.declare_queue("MONTREAL_stations_average")
    gc = GracefulKiller(pika)
    filter = Filter(pika)
    try:
        filter.run(trips_queue, stations_queue)
    except Exception as e:
        logging.error(f"Error consuming message: {e}")
