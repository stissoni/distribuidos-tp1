import logging
import os
import signal
import sys
import time
from haversine import haversine


class TripsHandler:
    def __init__(self, stations_handler, pika) -> None:
        self.logger = logging.getLogger("trips_handler")
        self.stations_handler = stations_handler
        self.pika = pika

    def get_distance_between_stations(self, start_code, end_code, year):
        distance = self.stations_handler.get_distance_between_stations(
            start_code, end_code, year
        )
        station_name = self.stations_handler.get_station_name(end_code, year)
        message = f"{station_name},{distance}"
        return message

    def callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        self.logger.info(f"Received message: {message[0:120]}...")
        header = message.split("|")[0]
        type = header.split(",")[0]
        rows = message.split("|")[1:]

        # Save message to disk in order to make the process fault tolerant
        with open("montreal_trips.txt", "a") as f:
            f.write(message + "\n")

        if type == "type=end_stream":
            self.logger.info("Received end_stream for montreal/trip")
            self.pika.publish(
                "type=end_stream", exchange="", routing_key="MONTREAL_stations_average"
            )
            self.pika.ack(method)
            self.pika.stop_consuming()
            return
        message = "type=stream_data"
        for row in rows:
            fields = row.split(",")
            fields = [field.split("=")[1] for field in fields]
            try:
                start_station_code = int(fields[1])
                end_station_code = int(fields[3])
                year = int(fields[6])
                station_distance_tuple = self.get_distance_between_stations(
                    start_station_code, end_station_code, year
                )
            except Exception as e:
                self.logger.error(
                    f"Error calculating distance between stations {start_station_code} and {end_station_code}. Error: {e}"
                )
                continue
            message += f"|{station_distance_tuple}"
        self.pika.publish(message, exchange="", routing_key="MONTREAL_stations_average")
        self.pika.ack(method)


class StationsHandler:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("stations_handler")
        self.pika = pika
        self.stations = {}
        self.distances = {}
        self.count_to_exit = 0

    def get_station_name(self, code, year):
        return self.stations[code][year]["name"]

    def calculate_distance(self, start_lat, start_lon, end_lat, end_lon):
        distance = haversine((start_lat, start_lon), (end_lat, end_lon))
        return distance

    def get_distance_between_stations(self, start_code, end_code, year):
        if start_code < end_code:
            key = (start_code, end_code, year)
        else:
            key = (end_code, start_code, year)
        if key in self.distances:
            return self.distances[key]
        else:
            distance = self.calculate_distance_between_stations(
                start_code, end_code, year
            )
            return distance

    def calculate_distance_between_stations(self, start_code, end_code, year):
        try:
            start_lat = self.stations[start_code][year]["lat"]
            start_lon = self.stations[start_code][year]["lon"]
            end_lat = self.stations[end_code][year]["lat"]
            end_lon = self.stations[end_code][year]["lon"]
        except KeyError:
            self.logger.error(f"{start_code} or {end_code} in year {year} not found")
            return 0
        distance = self.calculate_distance(start_lat, start_lon, end_lat, end_lon)
        if start_code < end_code:
            key = (start_code, end_code, year)
        else:
            key = (end_code, start_code, year)
        self.distances[key] = distance
        return distance

    def save_station(self, code, year, name, lat, lon, to_disk=True):
        self.logger.info(f"Saving station {code},{year},{name},{lat},{lon}")
        if code not in self.stations:
            self.stations[code] = {year: {"name": name, "lat": lat, "lon": lon}}
        elif year not in self.stations[code]:
            self.stations[code][year] = {"name": name, "lat": lat, "lon": lon}
        else:
            raise Exception(f"Station {code},{year} already exists")

        # Save data to disk in order to make the process fault tolerant
        if to_disk:
            with open("montreal_stations.txt", "a") as f:
                f.write(f"{code},{year},{name},{lat},{lon}\n")

    def callback(self, ch, method, properties, body):
        # Simulate a fault in the system at nth message from queue for debuggin

        self.count_to_exit += 1
        if self.count_to_exit == 5:
            sys.exit(-1)

        message = body.decode("utf-8")
        self.logger.info(f"Received message {self.count_to_exit}: {message[0:120]}...")
        header = message.split("|")[0]
        type = header.split(",")[0]
        table = header.split(",")[1]
        rows = message.split("|")[1:]

        if table != "table=montreal/station":
            self.logger.info("Ignoring message!")
            return
        elif type == "type=end_stream":
            self.logger.info("Received end_stream")
            self.pika.ack(method)
            self.pika.stop_consuming()
            return
        else:
            self.logger.info("Received message with MONTREAL stations")
            for row in rows:
                fields = row.split(",")
                fields = [field.split("=")[1] for field in fields]
                try:
                    code = int(fields[0])
                    name = fields[1]
                    lat = float(fields[2])
                    lon = float(fields[3])
                    year = int(fields[4])
                    self.save_station(code, year, name, lat, lon)
                except Exception as e:
                    self.logger.error(f"Error parsing row: {row}. Error: {e}")
                    continue

        print("SLEEPING FOR 10 SECONDS. KILL NOW!!!!!!!!!!!")
        time.sleep(10)

        self.pika.ack(method)


class Filter:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("montreal_filter")
        self.pika = pika

    def run(self, trips_queue, stations_queue):
        try:
            stations_handler = StationsHandler(self.pika)
            # Check if montreal_stations.txt exists, if so, load it else start consuming
            if os.path.exists("montreal_stations.txt"):
                self.logger.info("Loading stations from disk")
                with open("montreal_stations.txt", "r") as f:
                    for line in f:
                        fields = line.split(",")
                        fields = [field.strip() for field in fields]
                        code = int(fields[0])
                        year = int(fields[1])
                        name = fields[2]
                        lat = float(fields[3])
                        lon = float(fields[4])
                        print(
                            "Loading station information from disk",
                            code,
                            year,
                            name,
                            lat,
                            lon,
                        )
                        stations_handler.save_station(
                            code, year, name, lat, lon, to_disk=False
                        )
            trips_handler = TripsHandler(stations_handler, self.pika)
            self.pika.start_consuming(stations_queue, stations_handler.callback)
            # self.pika.start_consuming(trips_queue, trips_handler.callback)
        except Exception as e:
            self.logger.error(f"Error consuming message: {e}")
        finally:
            self.logger.info("Exiting gracefully")
            # self.pika.close()
