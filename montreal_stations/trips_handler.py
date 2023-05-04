import logging


class TripsHandler:
    def __init__(self, pika) -> None:
        self.logger = logging.getLogger("trips_handler")
        self.pika = pika
        self.trips = []
        self.total_trips = 0

    def get_trips(self):
        return self.trips

    def save_trip(self, start_station_code, end_station_code, year):
        self.trips.append((start_station_code, end_station_code, year))

    def callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        header = message.split("|")[0]
        rows = message.split("|")[1:]

        if "end_stream" in header:
            self.logger.info("Message contains end_stream: stopping consumption")
            self.pika.ack(method)
            self.pika.stop_consuming()
            return

        for row in rows:
            fields = row.split(",")
            try:
                start_station_code = int(fields[0])
                end_station_code = int(fields[1])
                year = int(fields[2])
                self.save_trip(start_station_code, end_station_code, year)
            except ValueError as e:
                self.logger.warning(
                    f"Error parsing the row: {row}. Error: {e}. Ignoring trip..."
                )
                continue
            except Exception as e:
                raise Exception(
                    f"Error parsing the following message: {message}. Error: {e}. Exiting..."
                )

        self.total_trips += len(rows)
        self.logger.info(f"Saving new trips records! Total trips: {self.total_trips}")
        self.pika.ack(method)
