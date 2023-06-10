import csv
import io
import logging
import os
from row import Row
import zipfile


ZIP_PATH = os.getenv("ZIP_PATH", "/app/data/data.zip")
BATCH_SIZE = 150


class Client:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("client")
        self.pika = pika

    def publish_to_queue(self, queue_name, message):
        self.pika.publish(message, exchange="", routing_key=queue_name)

    def stream_data(self, zip_file, data_files):
        for csv_file in data_files:
            with zip_file.open(csv_file) as csv_file:
                csv_reader = csv.reader(io.TextIOWrapper(csv_file))
                table_name = csv_file.name.rstrip(".csv")
                fields_names = next(csv_reader)
                rows_sended = 0
                message = f"type=stream_data,table={table_name}"
                for row in csv_reader:
                    row = Row(table=table_name, fields=fields_names, values=row)
                    message += f"|{str(row)}"
                    rows_sended += 1
                    if rows_sended == BATCH_SIZE:
                        self.publish_to_queue("CLIENT_queue", message)
                        message = f"type=stream_data,table={table_name}"
                        rows_sended = 0
                if rows_sended > 0:
                    self.publish_to_queue("CLIENT_queue", message)

                message = f"type=end_stream,table={table_name}"
                self.publish_to_queue("CLIENT_queue", message)

    def results_callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        header = message.split("|")[0]
        rows = message.split("|")[1:]
        # Write every rows element in a line in a file called "results_{header.split('=')[1]}.csv"
        with open(f"/app/data/results_{header.split('=')[1]}.csv", "w") as f:
            for row in rows:
                f.write(row + "\n")
        self.pika.ack(method)
        print(message)

    def start_streaming(self) -> None:
        self.logger.info("Starting streaming!")

        zip_file = zipfile.ZipFile(ZIP_PATH)
        csv_files = [file for file in zip_file.namelist() if file.endswith(".csv")]
        # Select first files ended with stations.csv
        stations_files = [file for file in csv_files if file.endswith("stations.csv")]
        self.stream_data(zip_file, stations_files)
        # Select first files ended with weather.csv
        weather_files = [file for file in csv_files if file.endswith("weather.csv")]
        self.stream_data(zip_file, weather_files)
        # Select first files ended with trips.csv
        trips_files = [file for file in csv_files if file.endswith("trips.csv")]
        self.stream_data(zip_file, trips_files)
        # Start consuming messages from result queue
        self.pika.start_consuming("CLIENT_results", self.results_callback)

    def run(self) -> None:
        try:
            self.logger.info("Starting client!")
            self.start_streaming()
        except Exception as e:
            raise Exception(f"Exception in client: {e}")
