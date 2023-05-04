import logging
from haversine import haversine
import itertools


class StationsHandler:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("stations_handler")
        self.pika = pika
        self.stations = {}
        self.distances = {}

    def get_stations(self):
        return self.stations

    def get_distance_between_stations(self, start_code, end_code, year):
        try:
            if start_code < end_code:
                key = (start_code, end_code, year)
            else:
                key = (end_code, start_code, year)
            return self.distances[key]
        except KeyError:
            return 0

    def get_station(self, code, year):
        if code not in self.stations:
            return None
        if year not in self.stations[code]:
            return None

        name = self.stations[code][year]["name"]
        lat = self.stations[code][year]["lat"]
        lon = self.stations[code][year]["lon"]
        return {"name": name, "lat": lat, "lon": lon}

    def save_station(self, code, year, name, lat, lon):
        self.logger.info(f"Saving station {code},{year},{name},{lat},{lon}")
        if code not in self.stations:
            self.stations[code] = {year: {"name": name, "lat": lat, "lon": lon}}
        elif year not in self.stations[code]:
            self.stations[code][year] = {"name": name, "lat": lat, "lon": lon}
        else:
            raise Exception(f"Station {code},{year} already exists")

    def calculate_distances(self):
        self.logger.info("Calculating unique codes per year...")
        unique_station_codes = {}
        for code in self.stations.keys():
            for year in self.stations[code].keys():
                if year not in unique_station_codes:
                    unique_station_codes[year] = set()
                unique_station_codes[year].add(code)
        self.logger.info("Calculating distances between stations...")
        i = 0
        for year in unique_station_codes.keys():
            self.logger.info(f"Calculating distances for year: {year}")
            unique_codes = unique_station_codes[year]
            combinations = itertools.combinations(unique_codes, 2)
            for start_code, end_code in combinations:
                if start_code < end_code:
                    key = (start_code, end_code, year)
                else:
                    key = (end_code, start_code, year)
                if key in self.distances:
                    self.logger.warning(
                        f"Already calculated: {key}. Total calculated: {i}"
                    )
                    i += 1
                    continue
                start_lat, start_lon = (
                    self.stations[start_code][year]["lat"],
                    self.stations[start_code][year]["lon"],
                )
                end_lat, end_lon = (
                    self.stations[end_code][year]["lat"],
                    self.stations[end_code][year]["lon"],
                )
                distance = haversine((start_lat, start_lon), (end_lat, end_lon))
                self.logger.info(
                    f"Calculated distance: {key} -> {distance}. Total calculated: {i}"
                )
                self.distances[key] = distance
                i += 1
        self.logger.info("Finished calculating distances")

    def callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        header = message.split("|")[0]
        if "end_stream" in header:
            self.logger.info("Message contains end_stream: stopping consumption")
            self.pika.ack(method)
            self.pika.stop_consuming()
            return

        row = message.split("|")[1]
        fields = row.split(",")
        if fields[0] == "table=montreal/station":
            fields = [fields.split("=")[1] for fields in fields]
            code = int(fields[1])
            name = fields[2]
            lat = float(fields[3])
            lon = float(fields[4])
            year = int(fields[5])
            self.save_station(code, year, name, lat, lon)

        self.pika.ack(method)
