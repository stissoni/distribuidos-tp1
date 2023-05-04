import logging
import signal
import sys
from filter import Filter
from pika_client import PikaClient


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        logging.info("action: receive_sigterm_signal | result: exiting gracefully!")
        sys.exit(0)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    pika = PikaClient("rabbit")
    pika.declare_exchange("weather", "fanout")
    weather_queue = pika.bind_to_exchange("weather")
    pika.declare_queue("rainy_filter")
    pika.declare_queue("rainy_trips")
    filter = Filter(pika)
    gc = GracefulKiller()
    try:
        filter.run(weather_queue)
    except:
        # Exiting gracefully
        sys.exit(0)
