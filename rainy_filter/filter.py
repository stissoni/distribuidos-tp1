import logging
from weather_handler import WeatherHandler
from trips_handler import TripsHandler


class Filter:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("rainy_filter")
        self.pika = pika

    def run(self, weather_queue):
        try:
            weather_handler = WeatherHandler(self.pika)
            trips_handler = TripsHandler(self.pika, weather_handler)
            self.logger.info("Starting to consume weather")
            self.pika.start_consuming(weather_queue, weather_handler.callback)
            trips_handler.obtain_rainy_days(weather_handler)
            self.logger.info("Starting to consume trips")
            self.pika.start_consuming("RAINY_montreal_trips", trips_handler.callback)
            self.pika.start_consuming("RAINY_toronto_trips", trips_handler.callback)
            self.pika.start_consuming("RAINY_washington_trips", trips_handler.callback)
            self.pika.publish(
                message="type=end_stream", exchange="", routing_key="RAINY_rainy_trips"
            )
        except Exception as e:
            self.logger.error(f"Error consuming message: {e}")
        finally:
            self.logger.info("Exiting gracefully")
            self.pika.close()
