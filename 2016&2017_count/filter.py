import logging
import os

TOTAL_WORKERS = int(os.getenv("TOTAL_WORKERS"))


class CountStations:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("count_stations")
        self.pika = pika
        self.stations = {}
        self.total_end_streams = 0
        self.total_trips = 0

    def count(self, station, year):
        if station not in self.stations:
            self.stations[station] = {year: 1}
        elif year not in self.stations[station]:
            self.stations[station][year] = 1
        else:
            self.stations[station][year] += 1

    def calculate_doubled_trips(self):
        # Calculate the stations that doubled the trips between 2016 and 2017
        doubled_trips = []
        for station in self.stations:
            trips_2016 = self.stations[station].get("2016", 0)
            trips_2017 = self.stations[station].get("2017", 0)
            if (trips_2016 > 0) and (trips_2017 > 0) and (trips_2017 > 2 * trips_2016):
                doubled_trips.append(station)
        message = "type=result_query_doubled_trips"
        for station in doubled_trips:
            self.logger.info(
                f"Station {station} has {self.stations[station]['2016']} trips in 2016 and {self.stations[station]['2017']} trips in 2017"
            )
            message += f"|station={station},2016={self.stations[station]['2016']},2017={self.stations[station]['2017']}"
        return message

    def callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        message = message.split("|")
        header = message[0]
        rows = message[1:]

        if "end_stream" in header:
            self.total_end_streams += 1
            self.logger.info(
                f"Message contains end_stream. Total end_stream received: {self.total_end_streams}"
            )
            if self.total_end_streams == TOTAL_WORKERS:
                self.logger.info("All workers finished. Calculating doubled trips...")
                self.pika.ack(method)
                self.pika.stop_consuming()
            return

        for row in rows:
            if row == "":
                continue
            fields = row.split(",")
            station = fields[0]
            year = fields[1]
            self.count(station, year)
        self.total_trips += len(rows)
        self.logger.info(f"Processing new trips records! Total: {self.total_trips}")
        self.pika.ack(method)


class Filter:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("filter_count_stations")
        self.pika = pika

    def run(self, my_queue):
        try:
            count_stations = CountStations(self.pika)
            self.logger.info(f"Starting to consume messages from {my_queue}")
            self.pika.start_consuming(my_queue, count_stations.callback)

            results = count_stations.calculate_doubled_trips()
            self.logger.info("Publishing results...")
            self.pika.publish(message=results, exchange="", routing_key="query_results")
        except Exception as e:
            self.logger.error(f"Error consuming message: {e}")
        finally:
            self.logger.info("Exiting gracefully")
            self.pika.close()
