import logging
import os

TRIPS_FILTER_REPLICAS = os.getenv("TRIPS_FILTER_REPLICAS", 1)


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
            self.total_end_streams += 1
            self.logger.info(
                f"Message contains end_stream. Count {self.total_end_streams}"
            )
            if self.total_end_streams == 3:
                stop = True
            if self.total_end_streams == ((int(TRIPS_FILTER_REPLICAS) * 3) + 3):
                self.logger.info("All end_stream messages received")
                message = "type=end_stream"
                self.pika.publish(
                    message, exchange="", routing_key="20162017_count_stations"
                )
                stop = True
        else:
            if "station" in header:
                self.logger.info("Message contains station")
                for row in rows:
                    values = [field.split("=")[1] for field in row.split(",")]
                    code = values[0]
                    name = values[1]
                    year = values[4]
                    city = header.split(",")[1].split("=")[1].split("/")[0]
                    try:
                        if city not in self.stations:
                            self.stations[city] = {}
                        if year not in self.stations[city]:
                            self.stations[city][year] = {}
                        if code not in self.stations[city][year]:
                            self.stations[city][year][code] = {}
                        self.stations[city][year][code] = {"name": name}
                    except Exception as e:
                        self.logger.error(f"Error adding station: {e}")
            else:
                message = "type=stream_data"
                for row in rows:
                    values = [field.split("=")[1] for field in row.split(",")]
                    start_station_code = values[0]
                    city = values[1]
                    year = values[2]
                    try:
                        name = self.stations[city][year][start_station_code]["name"]
                    except Exception as e:
                        self.logger.error(f"Error getting station: {e}")
                        return
                    message += f"|name={name},year={year}"
                if message != "type=stream_data":
                    self.pika.publish(
                        message, exchange="", routing_key="20162017_count_stations"
                    )
        self.pika.ack(method)
        if stop:
            self.pika.stop_consuming()

    def run(self, stations_queue, filter_queue, next_step_queue):
        try:
            self.next_step_queue = next_step_queue
            self.pika.start_consuming(stations_queue, self.callback)
            self.pika.start_consuming(filter_queue, self.callback)
        except Exception as e:
            self.logger.error(f"Error consuming message: {e}")
        finally:
            self.logger.info("Exiting gracefully")
            self.pika.close()
            return
