#!/usr/bin/env python3
from driver import Driver
from pika_client import PikaClient
from gracefull_killer import GracefulKiller
import logging

RABBIT_HOST = "rabbit"


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    pika = PikaClient(RABBIT_HOST)
    # Create queues and exchanges
    pika.declare_queue("client_queue")

    pika.declare_queue("MONTREAL_montreal_trips")
    pika.declare_queue("MONTREAL_stations_average")

    pika.declare_queue("RAINY_montreal_trips")
    pika.declare_queue("RAINY_toronto_trips")
    pika.declare_queue("RAINY_washington_trips")
    pika.declare_queue("RAINY_rainy_trips")

    pika.declare_queue("20162017_montreal_trips")
    pika.declare_queue("20162017_toronto_trips")
    pika.declare_queue("20162017_washington_trips")
    pika.declare_queue("20162017_join_filter")
    pika.declare_queue("20162017_count_stations")

    pika.declare_exchange("weather")
    pika.declare_exchange("stations")

    driver = Driver(pika)
    gk = GracefulKiller(pika)
    try:
        driver.run()
    except Exception as e:
        logging.exception(f"Exception in client: {e}")
