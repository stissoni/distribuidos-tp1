import logging


class Filter:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("montreal_filter")
        self.pika = pika

    def callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        self.logger.debug(f"Received message: {message}")

        stop = False
        header = message.split("|")[0]
        rows = message.split("|")[1:]

        if "end_stream" in header:
            self.logger.info("Message contains end_stream")
            stop = True
        message = "type=stream_data"
        for row in rows:
            fields = row.split(",")
            if fields[0] == "table=montreal/trip":
                start_station_code = fields[1].split("=")[1]
                end_station_code = fields[2].split("=")[1]
                year = fields[3].split("=")[1]
                message += f"|{start_station_code},{end_station_code},{year}"
        if message != "type=stream_data":
            self.logger.info("Redirecting message to montral filter...")
            self.pika.publish(
                message=message, exchange="", routing_key="montreal_trips"
            )
        else:
            self.logger.info("Message does not contain montral trips. Ignoring...")
        self.pika.ack(method)
        if stop:
            self.pika.stop_consuming()
            return

    def run(self):
        try:
            self.pika.start_consuming("montreal_filter", self.callback)
            self.pika.publish(
                message="type=end_stream", exchange="", routing_key="montreal_trips"
            )
        except Exception as e:
            self.logger.error(f"Error consuming message: {e}")
        finally:
            self.logger.info("Exiting gracefully")
            self.pika.close()
