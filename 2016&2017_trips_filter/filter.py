import logging


class Filter:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("2016&2017_filter")
        self.pika = pika
        self.total_end_streams = 0
        self.stations = {}

    def callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        self.logger.info(f"Received message: {message[0:120]}...")

        stop = False
        message = message.split("|")
        header = message[0]
        rows = message[1:]

        if "end_stream" in header:
            self.logger.info("Message contains end_stream")
            message = "type=end_stream"
            self.pika.publish(message, exchange="", routing_key="20162017_join_filter")
            stop = True
        else:
            message = "type=stream_data"
            for row in rows:
                values = [field.split("=")[1] for field in row.split(",")]
                start_station_code = values[1]
                year = values[6]
                city = header.split(",")[1].split("=")[1].split("/")[0]
                if year == "2016" or year == "2017":
                    message += f"|code={start_station_code},city={city},year={year}"
            if message != "type=stream_data":
                self.pika.publish(
                    message, exchange="", routing_key="20162017_join_filter"
                )
        self.pika.ack(method)
        if stop:
            self.pika.stop_consuming()

    def run(self, stations_queue, filter_queue, next_step_queue):
        try:
            self.next_step_queue = next_step_queue
            self.pika.start_consuming("20162017_montreal_trips", self.callback)
            self.pika.start_consuming("20162017_toronto_trips", self.callback)
            self.pika.start_consuming("20162017_washington_trips", self.callback)
        except Exception as e:
            self.logger.error(f"Error consuming message: {e}")
        finally:
            self.logger.info("Exiting gracefully")
            self.pika.close()
            return
