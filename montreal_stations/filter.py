import logging
import sys
from threading import Thread
from stations_handler import StationsHandler
from trips_handler import TripsHandler
from multiprocessing import Pool


class MontrealAverages:
    def __init__(self) -> None:
        self.logger = logging.getLogger("montreal_stations_avg")

    def calculate_avg(self, trips_handler, stations_handler):
        trips = trips_handler.get_trips()
        i = 0
        total = len(trips)
        distances = {}

        for trip in trips:
            try:
                start_station_code = trip[0]
                end_station_code = trip[1]
                year = trip[2]
                end_station_name = stations_handler.get_station(end_station_code, year)[
                    "name"
                ]
                self.logger.info(
                    f"Obtaining distance trip {i}/{total}: {end_station_name}"
                )
                distance = stations_handler.get_distance_between_stations(
                    start_station_code, end_station_code, year
                )
                if end_station_name not in distances:
                    distances[end_station_name] = []
                distances[end_station_name].append(distance)
            except Exception as e:
                self.logger.warning(
                    f"Error obtaining distance for trip {trip}. Error: {e}. Skipping..."
                )
                pass
            i += 1

        self.logger.info("Calculating averages...")
        avgs = {
            end_station_name: sum(distances[end_station_name])
            / len(distances[end_station_name])
            for end_station_name in distances.keys()
        }
        self.logger.info("Obtaining stations with average distance > 6 km...")
        more_than_6 = [
            (end_station_name, avg) for end_station_name, avg in avgs.items() if avg > 6
        ]
        self.logger.info(f"Averages for stations: {avgs}")
        self.logger.info(f"Stations with average distance > 6 km: {more_than_6}")
        return more_than_6


class Filter:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("montreal_avg")
        self.pika = pika

    def run(self, stations_queue):
        try:
            stations_handler = StationsHandler(self.pika)
            trips_handler = TripsHandler(self.pika)
            self.logger.info("Consuming from stations queue")
            self.pika.start_consuming(stations_queue, stations_handler.callback)
            # create a thread and start calculating distances in parallel
            thread = Thread(target=stations_handler.calculate_distances)
            thread.start()
            self.logger.info("Consuming from trips queue")
            self.pika.start_consuming("montreal_trips", trips_handler.callback)
            # wait for the thread to finish
            thread.join()
            mtrl_avg = MontrealAverages()
            results = mtrl_avg.calculate_avg(trips_handler, stations_handler)
            self.logger.info("Publishing results...")
            self.pika.publish(
                message=str(results), exchange="", routing_key="query_results"
            )
        except Exception as e:
            self.logger.error(f"Error consuming message: {e}")
        finally:
            self.logger.info("Exiting gracefully")
            thread.terminate()
            try:
                self.pika.close()
            except:
                sys.exit(0)
