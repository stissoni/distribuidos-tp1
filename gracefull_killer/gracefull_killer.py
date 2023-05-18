import logging
import signal


class GracefulKiller:
    def __init__(self, pika):
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.pika = pika

    def exit_gracefully(self, *args):
        logging.info("Received SIGTERM signal. Closing pika connection...")
        self.pika.close()
