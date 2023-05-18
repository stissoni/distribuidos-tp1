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
    my_queue = pika.declare_queue("20162017_count_stations")
    results_queue = pika.declare_queue("CLIENT_results")
    filter = Filter(pika)
    gc = GracefulKiller(pika)
    try:
        filter.run(my_queue)
    except Exception as e:
        logging.error(f"Error consuming message: {e}")
