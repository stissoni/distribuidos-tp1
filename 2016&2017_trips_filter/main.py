import logging
from filter import Filter
from pika_client import PikaClient
from gracefull_killer import GracefulKiller


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    pika = PikaClient("rabbit")
    stations_queue = pika.bind_to_exchange("stations")
    filter_queue = pika.declare_queue("20162017_filter")
    next_step_queue = pika.declare_queue("20162017_count_stations")

    filter = Filter(pika)
    gc = GracefulKiller(pika)
    try:
        filter.run(stations_queue, filter_queue, next_step_queue)
    except Exception as e:
        logging.error(f"Error consuming message: {e}")
