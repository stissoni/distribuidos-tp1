import logging
import os

RAINY_FILTER_REPLICAS = os.getenv("RAINY_FILTER_REPLICAS", 1)


class DurationAverages:
    def __init__(self) -> None:
        self.logger = logging.getLogger("rainy_durations_avg")
        self.total_end_streams = 0
        self.rain = {}

    def calculate_avg(self):
        self.logger.info("Calculating average...")
        avg = {date: sum(rain) / len(rain) for date, rain in self.rain.items()}
        self.logger.info(f"Results: {avg}")
        return avg

    def callback(self, ch, method, properties, body):
        message = body.decode("utf-8")
        self.logger.info(f"Received message: {message}")

        fields = message.split(",")
        if "end_stream" in fields[0]:
            self.logger.info("Message contains end_stream")
            self.total_end_streams += 1
            if self.total_end_streams == int(RAINY_FILTER_REPLICAS):
                self.logger.info("All replicas have sent end_stream")
                ch.stop_consuming()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        else:
            date = fields[0]
            rain = fields[1]
            if date not in self.rain:
                self.rain[date] = []
            self.rain[date].append(float(rain))
        ch.basic_ack(delivery_tag=method.delivery_tag)


class Filter:
    def __init__(self) -> None:
        self.logger = logging.getLogger("montreal_avg_filter")

    def run(self, pika):
        try:
            rainy_trips_avg = DurationAverages()
            pika.start_consuming("RAINY_rainy_trips", rainy_trips_avg.callback)
            results = rainy_trips_avg.calculate_avg()
            self.logger.info("Publishing results...")
            message = "type=rainy_query"
            for date, avg in results.items():
                message += f"|{date},{avg}"
            pika.publish(message=message, exchange="", routing_key="CLIENT_results")
        except Exception as e:
            self.logger.error(f"Error consuming message: {e}")
        finally:
            self.logger.info("Exiting gracefully")
            pika.close()
