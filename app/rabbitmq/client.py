import json
from typing import Dict, Any

import pika
from fastapi import BackgroundTasks
from pika.exceptions import AMQPError

from app.common.storage import rabbitmq_messages
from app.rabbitmq.config import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_QUEUE


# RabbitMQ Producer
def publish_to_rabbitmq(message: Dict[str, Any], queue: str = RABBITMQ_QUEUE) -> bool:
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
        )
        channel = connection.channel()

        channel.queue_declare(queue=queue, durable=True)

        channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )

        connection.close()
        return True
    except AMQPError as e:
        print(f"Failed to publish to RabbitMQ: {e}")
        return False

# RabbitMQ Consumer
def consume_rabbitmq_messages(background_tasks: BackgroundTasks):
    def callback(ch, method, properties, body):
        message = json.loads(body)
        rabbitmq_messages.append(message)
        print(f"Received RabbitMQ message: {message}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def consume():
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
            )
            channel = connection.channel()

            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)

            print("RabbitMQ consumer started. Waiting for messages...")
            channel.start_consuming()
        except AMQPError as e:
            print(f"RabbitMQ consumer error: {e}")

    background_tasks.add_task(consume)
