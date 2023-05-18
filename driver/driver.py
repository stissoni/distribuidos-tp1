import logging
import os

MONTREAL_FILTER_REPLICAS = int(os.getenv("MONTREAL_FILTER_REPLICAS", 1))
TRIPS_FILTER_REPLICAS_2016_2017 = int(os.getenv("TRIPS_FILTER_2016_2017_REPLICAS", 1))
RAINY_FILTER_REPLICAS = int(os.getenv("RAINY_FILTER_REPLICAS", 1))


class Driver:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("driver")
        self.pika = pika
        self.end_streams = {}

    def publish_end_stream(self, queue, table, times=1):
        message = f"type=end_stream,table={table}"
        for i in range(times):
            self.pika.publish(message, exchange="", routing_key=queue)

    def handle_stations(self, message_type, table, message):
        if message_type == "type=end_stream":
            self.end_streams[table] = True
        self.pika.publish(message, exchange="stations", routing_key="")

    def handle_weather(self, message_type, table, message):
        if message_type == "type=end_stream":
            self.end_streams[table] = True
        self.pika.publish(message, exchange="weather", routing_key="")

    def handle_trips(self, message_type, table, message):
        if message_type == "type=end_stream":
            self.end_streams[table] = True
            for queue in self.get_queues_from_table(table):
                if queue == "MONTREAL_montreal_trips":
                    self.publish_end_stream(
                        queue, table, times=MONTREAL_FILTER_REPLICAS
                    )
                if queue == "20162017_montreal_trips":
                    self.publish_end_stream(
                        queue, table, times=TRIPS_FILTER_REPLICAS_2016_2017
                    )
                if queue == "20162017_toronto_trips":
                    self.publish_end_stream(
                        queue, table, times=TRIPS_FILTER_REPLICAS_2016_2017
                    )
                if queue == "20162017_washington_trips":
                    self.publish_end_stream(
                        queue, table, times=TRIPS_FILTER_REPLICAS_2016_2017
                    )
                if queue == "RAINY_montreal_trips":
                    self.publish_end_stream(queue, table, times=RAINY_FILTER_REPLICAS)
                if queue == "RAINY_toronto_trips":
                    self.publish_end_stream(queue, table, times=RAINY_FILTER_REPLICAS)
                if queue == "RAINY_washington_trips":
                    self.publish_end_stream(queue, table, times=RAINY_FILTER_REPLICAS)
                else:
                    self.publish_end_stream(queue, table, times=1)
        else:
            for queue in self.get_queues_from_table(table):
                self.pika.publish(message, exchange="", routing_key=queue)

    def get_queues_from_table(self, table):
        if table == "table=montreal/trip":
            return [
                "MONTREAL_montreal_trips",
                "20162017_montreal_trips",
                "RAINY_montreal_trips",
            ]
        if table == "table=toronto/trip":
            return ["20162017_toronto_trips", "RAINY_toronto_trips"]
        if table == "table=washington/trip":
            return ["20162017_washington_trips", "RAINY_washington_trips"]

    def callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        header = message.split("|")[0]
        type = header.split(",")[0]
        table = header.split(",")[1]

        self.logger.info(f"Received message {type},{table}")

        if "weather" in table:
            self.handle_weather(type, table, message)
        elif "station" in table:
            self.handle_stations(type, table, message)
        else:
            self.handle_trips(type, table, message)

        self.pika.ack(method)
        if len(self.end_streams) == 9:
            self.pika.stop_consuming()

    def run(self):
        self.pika.start_consuming("client_queue", self.callback)
