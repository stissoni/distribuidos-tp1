import logging
import datetime


class WeatherHandler:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("weather_handler")
        self.pika = pika
        self.total_end_stream = 0
        self.weather = {}
        self.rainy_days = {"montreal": [], "washington": [], "toronto": []}

    def update_rainy_days(self, city):
        for date, rain in self.weather.get(city, {}).items():
            if rain > 30 and date not in self.rainy_days[city]:
                self.rainy_days[city].append(date)

    def get_weather(self, city, date):
        return self.weather.get(city, {}).get(date, 0)

    def get_rainy_days(self):
        return self.rainy_days

    def save_weather(self, city, date, rain):
        if city not in self.weather:
            self.weather[city] = {}
        self.weather[city][date] = rain

    def callback(self, ch, method, properties, body):
        message = body.decode("utf-8")

        header = message.split("|")[0]
        rows = message.split("|")[1:]

        if "end_stream" in header:
            self.logger.info(f"Message contains end_stream: {self.total_end_stream}")
            self.total_end_stream += 1
            if self.total_end_stream == 3:
                self.logger.info(
                    "Received all end_stream messages: stopping consumption"
                )
                self.pika.stop_consuming()
            self.pika.ack(method)
            return

        for row in rows:
            fields = row.split(",")
            city = header.split(",")[1].split("=")[1].split("/")[0]
            day = datetime.datetime.strptime(fields[0].split("=")[1], "%Y-%m-%d").date()
            day_before = (day - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            day_rain = float(fields[1].split("=")[1])
            self.logger.info(
                f"Saving weather information {city},{day_before},{day_rain}"
            )
            self.save_weather(city, day_before, day_rain)
            self.update_rainy_days(city)
        self.pika.ack(method)
