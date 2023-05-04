import csv
import io
import logging
import os
import signal
import sys
from time import sleep
from row import Row
import zipfile


ZIP_PATH = os.getenv("ZIP_PATH", "/app/data/data.zip")
BATCH_SIZE = 200


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        logging.info("action: receive_sigterm_signal | result: exiting gracefully!")
        raise Exception("Exiting gracefully!")


class Client:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("driver")
        self.pika = pika

    def publish_to_queue(self, queue_name, message):
        self.logger.info(f"Streaming {message[0:120]}...")
        self.pika.publish(message, exchange="", routing_key=queue_name)

    def publish_to_exchange(self, exchange_name, message):
        self.logger.info(f"Streaming {message} to exchange {exchange_name}")
        self.pika.publish(message, exchange=exchange_name, routing_key="")

    def stream_data(self, zip_file, data_files, exchange):
        for csv_file in data_files:
            with zip_file.open(csv_file) as csv_file:
                csv_reader = csv.reader(io.TextIOWrapper(csv_file))
                table_name = csv_file.name.rstrip(".csv")
                fields_names = next(csv_reader)
                for row in csv_reader:
                    row = str(Row(table=table_name, fields=fields_names, values=row))
                    message = f"type=stream_data|{row}"
                    self.publish_to_exchange(exchange, message)

        message = "type=end_stream"
        self.publish_to_exchange(exchange, message)

    def stream_trips(self, zip_file, trips_files):
        for csv_file in trips_files:
            self.logger.info(f"Streaming data from {csv_file}!")
            with zip_file.open(csv_file) as csv_file:
                csv_reader = csv.reader(io.TextIOWrapper(csv_file))
                table_name = csv_file.name.rstrip(".csv")
                next(csv_reader)
                trips = 0
                message_20162017 = "type=stream_data"
                message_montreal = "type=stream_data"
                message_rainy = "type=stream_data"
                # Row format:start_date,start_station_code,end_date,end_station_code,duration_sec,is_member,yearid
                for row in csv_reader:
                    offset = 0
                    start_date = row[0 + offset]
                    start_station_code = row[1 + offset]
                    end_station_code = row[3 + offset]
                    duration_sec = row[4 + offset]
                    year = row[6 + offset]
                    # Filtering fields for each filter
                    message_20162017 += f"|table={table_name},year={year},start_station_code={start_station_code}"
                    message_montreal += f"|table={table_name},start_station_code={start_station_code},end_station_code={end_station_code},year={year}"
                    message_rainy += f"|table={table_name},start_date={start_date},duration_sec={duration_sec}"
                    # Acummulate trips for message
                    trips += 1
                    if trips < BATCH_SIZE:
                        continue
                    # Publish messages
                    # For 2016&2017_filter
                    self.publish_to_queue("2016&2017_filter", message_20162017)
                    # For rainy_filter
                    self.publish_to_queue("rainy_filter", message_rainy)
                    # For montreal_filter
                    self.publish_to_queue("montreal_filter", message_montreal)

                    trips = 0
                    message_20162017 = "type=stream_data"
                    message_montreal = "type=stream_data"
                    message_rainy = "type=stream_data"

                if trips > 0:
                    # There are some trips that were not published in previous loop
                    self.publish_to_queue("2016&2017_filter", message_20162017)
                    self.publish_to_queue("rainy_filter", message_rainy)
                    self.publish_to_queue("montreal_filter", message_montreal)

        message = "type=end_stream"
        i = 0
        while True:
            self.pika.publish(message, exchange="", routing_key="2016&2017_filter")
            self.pika.publish(message, exchange="", routing_key="rainy_filter")
            self.pika.publish(message, exchange="", routing_key="montreal_filter")
            sleep(10)
            i += 1
            if i == 10:
                return

    def results_callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        print(message)

    def start_streaming(self) -> None:
        self.logger.info("Starting streaming!")

        zip_file = zipfile.ZipFile(ZIP_PATH)
        csv_files = [file for file in zip_file.namelist() if file.endswith(".csv")]
        # Select first files ended with stations.csv
        stations_files = [file for file in csv_files if file.endswith("stations.csv")]
        self.stream_data(zip_file, stations_files, "stations")
        # Select first files ended with weather.csv
        weather_files = [file for file in csv_files if file.endswith("weather.csv")]
        self.stream_data(zip_file, weather_files, "weather")
        # Select first files ended with trips.csv
        trips_files = [file for file in csv_files if file.endswith("trips.csv")]
        self.stream_trips(zip_file, trips_files)
        # Start consuming messages from result queue
        self.pika.start_consuming("query_results", self.results_callback)

    def run(self) -> None:
        try:
            self.logger.info("Starting client!")
            self.start_streaming()
        except:
            self.logger.info("Exiting gracefully!")
            raise Exception("Exception in client! Exiting gracefully")
