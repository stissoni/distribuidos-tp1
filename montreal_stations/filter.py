import logging
import os

MONTREAL_FILTER_REPLICAS = int(os.getenv("MONTREAL_FILTER_REPLICAS", 1))


class MontrealAverages:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("montreal_stations_avg")
        self.pika = pika
        self.count_end_streams = 0
        self.distances = {}
        self.averages = {}

    def publish_query_results(self):
        results = self.calculate_average()
        self.logger.info("Publishing query results!")
        message = "type=montreal_query"
        for tuple in results:
            station = tuple[0]
            average = tuple[1]
            message += f"|{station},{average}"
        self.pika.publish(message, exchange="", routing_key="CLIENT_results")

    def callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        header = message.split("|")[0]
        rows = message.split("|")[1:]

        if header == "type=end_stream":
            self.count_end_streams += 1
            self.logger.info(f"Received end_stream. Count: {self.count_end_streams}")
            if self.count_end_streams == MONTREAL_FILTER_REPLICAS:
                self.publish_query_results()
                self.pika.stop_consuming()
            self.pika.ack(method)
            return
        for row in rows:
            station = row.split(",")[0]
            distance = float(row.split(",")[1])
            if station not in self.distances:
                self.distances[station] = []
            self.distances[station].append(distance)
        self.pika.ack(method)

    def calculate_average(self):
        result = {
            end_station_name: sum(distances) / len(distances)
            for end_station_name, distances in self.distances.items()
        }
        more_than_6 = [
            (end_station_name, avg)
            for end_station_name, avg in result.items()
            if avg > 6
        ]
        self.logger.info(f"Stations with average distance > 6 km: {more_than_6}")
        return more_than_6


class Filter:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("montreal_avg")
        self.pika = pika

    def run(self):
        try:
            mtrl_avg = MontrealAverages(self.pika)
            self.pika.start_consuming("MONTREAL_stations_average", mtrl_avg.callback)
        except Exception as e:
            self.logger.error(f"Error consuming message: {e}")
        finally:
            self.logger.info("Exiting gracefully")
            self.pika.close()
