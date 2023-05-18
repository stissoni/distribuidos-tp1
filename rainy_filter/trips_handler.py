import logging


class TripsHandler:
    def __init__(self, pika, weather_handler) -> None:
        self.logger = logging.getLogger("trips_handler")
        self.pika = pika
        self.rainy_days = None

    def obtain_rainy_days(self, weather_handler):
        self.logger.info(
            f"Obtained rainy days from weather handler: {weather_handler.rainy_days}"
        )
        self.rainy_days = weather_handler.get_rainy_days()

    def calculate_trip_rain(self, city, date, duration):
        if date in self.rainy_days[city]:
            self.logger.info(
                f"Trip {city},{date},{duration} was rainy. Redirecting message!"
            )
            message = f"{date},{duration}"
            self.pika.publish(
                message=message, exchange="", routing_key="RAINY_rainy_trips"
            )
            return

    def callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        header = message.split("|")[0]
        rows = message.split("|")[1:]

        if "end_stream" in header:
            self.logger.info("Message contains end_stream: stopping consumption")
            self.pika.stop_consuming()
            self.pika.ack(method)
            return

        for row in rows:
            fields = row.split(",")
            city = header.split(",")[1].split("=")[1].split("/")[0]
            start_date = fields[0].split("=")[1].split(" ")[0]
            duration_sec = float(fields[4].split("=")[1])
            if duration_sec < 0:
                duration_sec = 0
            self.calculate_trip_rain(city, start_date, duration_sec)
        self.pika.ack(method)
