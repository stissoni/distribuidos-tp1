import pika


class PikaClient:
    def __init__(self, host):
        self.host = host
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host)
        )
        self.channel = self.connection.channel()

    def publish(self, message, exchange="", routing_key=""):
        self.channel.basic_publish(
            exchange=exchange, routing_key=routing_key, body=message
        )

    def declare_queue(self, name, durable=True):
        self.channel.queue_declare(queue=name, durable=durable)
        return name

    def declare_exchange(self, name, exchange_type="fanout"):
        self.channel.exchange_declare(exchange=name, exchange_type=exchange_type)

    def bind_to_exchange(self, exchange):
        result = self.channel.queue_declare(queue="", exclusive=True)
        queue = result.method.queue
        self.channel.queue_bind(exchange=exchange, queue=queue)
        return queue

    def start_consuming(self, queue, callback):
        self.channel.basic_consume(queue=queue, on_message_callback=callback)
        self.channel.start_consuming()

    def stop_consuming(self):
        self.channel.stop_consuming()

    def ack(self, method):
        self.channel.basic_ack(delivery_tag=method.delivery_tag)

    def close(self):
        self.connection.close()
