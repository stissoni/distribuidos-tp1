import logging
from filter import Filter
from pika_client import PikaClient
from gracefull_killer import GracefulKiller


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    pika = PikaClient("rabbit")
    pika.declare_queue("RAINY_rainy_trips")
    filter = Filter()
    gc = GracefulKiller(pika)
    try:
        filter.run(pika)
    except Exception as e:
        logging.error(f"Error consuming message: {e}")
