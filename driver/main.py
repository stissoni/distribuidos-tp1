#!/usr/bin/env python3
import sys
from driver import Driver
from pika_client import PikaClient
from gracefull_killer import GracefulKiller
import logging
import os

RABBIT_HOST = "rabbit"
MONTREAL_FILTER_REPLICAS = int(os.getenv("MONTREAL_FILTER_REPLICAS", 1))
TRIPS_FILTER_REPLICAS_2016_2017 = int(os.getenv("TRIPS_FILTER_2016_2017_REPLICAS", 1))
RAINY_FILTER_REPLICAS = int(os.getenv("RAINY_FILTER_REPLICAS", 1))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    pika = PikaClient(RABBIT_HOST)
    gk = GracefulKiller(pika)
    driver = Driver(pika)
    # Create queues and exchanges
    pika.declare_queue("CLIENT_queue")
    pika.declare_queue("CLIENT_results")

    # Declare exchanges
    stations_exchange = pika.declare_exchange("STATIONS_exchange")
    weather_exchange = pika.declare_exchange("WEATHER_exchange")
    driver.set_weather_exchange(weather_exchange)
    driver.set_stations_exchange(stations_exchange)

    # Montreal query queues
    pika.declare_queue("MONTREAL_montreal_trips")
    pika.declare_queue("MONTREAL_stations_average")
    for i in range(MONTREAL_FILTER_REPLICAS):
        queue_name = pika.declare_queue(f"MONTREAL_stations_filter_{i+1}")
        pika.bind_queue_to_exchange(queue_name, stations_exchange)

    # Rainy query queues
    pika.declare_queue("RAINY_montreal_trips")
    pika.declare_queue("RAINY_toronto_trips")
    pika.declare_queue("RAINY_washington_trips")
    for i in range(RAINY_FILTER_REPLICAS):
        queue_name = pika.declare_queue(f"RAINY_weather_filter_{i+1}")
        pika.bind_queue_to_exchange(queue_name, weather_exchange)

    # Trips 2016-2017 query queues
    pika.declare_queue("20162017_montreal_trips")
    pika.declare_queue("20162017_toronto_trips")
    pika.declare_queue("20162017_washington_trips")
    pika.declare_queue("20162017_join_filter")
    pika.declare_queue("20162017_count_stations")
    for i in range(TRIPS_FILTER_REPLICAS_2016_2017):
        queue_name = pika.declare_queue(f"20162017_stations_filter_{i+1}")
        pika.bind_queue_to_exchange(queue_name, stations_exchange)

    try:
        if len(sys.argv) > 1:
            query = sys.argv[1]
            driver.run(query)
        else:
            driver.run()
    except Exception as e:
        logging.exception(f"Exception in client: {e}")
