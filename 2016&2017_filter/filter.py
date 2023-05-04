import logging


class Filter:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("2016&2017_filter")
        self.pika = pika
        self.stations = {}

    def save_station(self, city, code, name, year):
        self.logger.info(f"Received station: {city}, {code}, {name}, {year}")
        if city not in self.stations:
            self.stations[city] = {}
        if code not in self.stations[city]:
            self.stations[city][code] = {}
        if year not in self.stations[city][code]:
            self.stations[city][code][year] = name
        else:
            raise Exception(f"Station {code} already exists")

    def callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        self.logger.info(f"Received message: {message[0:120]}...")

        stop = False
        message = message.split("|")
        header = message[0]
        rows = message[1:]

        if "end_stream" in header:
            self.logger.info("Message contains end_stream")
            stop = True
        else:
            message = ""
            for row in rows:
                fields = row.split(",")
                if "/station" in fields[0]:
                    city = fields[0].split("=")[1].split("/")[0]
                    code = fields[1].split("=")[1]
                    name = fields[2].split("=")[1]
                    year = fields[5].split("=")[1]
                    if year == "2016" or year == "2017":
                        self.save_station(city, code, name, year)
                        continue
                elif "/trip" in fields[0]:
                    year = fields[1].split("=")[1]
                    if year != "2016" and year != "2017":
                        continue
                    city = fields[0].split("=")[1].split("/")[0]
                    start_station_code = fields[2].split("=")[1]
                    station_name = self.stations[city][start_station_code][year]
                    message += f"|{station_name},{year}"
            if message != "":
                self.pika.publish(
                    message=message, exchange="", routing_key=self.next_step_queue
                )
                self.logger.debug(f"Message redirected: {message}")

        self.pika.ack(method)
        if stop:
            self.pika.stop_consuming()
            return

    def run(self, stations_queue, filter_queue, next_step_queue):
        try:
            self.next_step_queue = next_step_queue
            self.pika.start_consuming(stations_queue, self.callback)
            self.pika.start_consuming(filter_queue, self.callback)
            self.pika.publish(
                "type=end_stream", exchange="", routing_key=self.next_step_queue
            )
        except Exception as e:
            self.logger.error(f"Error consuming message: {e}")
        finally:
            self.logger.info("Exiting gracefully")
            self.pika.close()
            return
