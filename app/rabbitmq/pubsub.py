import json
import uuid
from typing import Dict, Any, List, Optional

import pika
from fastapi import BackgroundTasks
from pika.exceptions import AMQPError

from app.common.storage import pubsub_messages
from app.rabbitmq.config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_PUBSUB_EXCHANGE,
    RABBITMQ_PUBSUB_QUEUE_PREFIX
)


# RabbitMQ Publisher for Pub/Sub pattern
def publish_to_exchange(message: Dict[str, Any], exchange: str = RABBITMQ_PUBSUB_EXCHANGE) -> bool:
    """
    Publish a message to a RabbitMQ exchange using the Publish/Subscribe pattern.
    
    Args:
        message: The message to publish
        exchange: The name of the exchange to publish to (default: RABBITMQ_PUBSUB_EXCHANGE)
        
    Returns:
        bool: True if the message was published successfully, False otherwise
    """
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
        )
        channel = connection.channel()

        # Declare a fanout exchange
        channel.exchange_declare(exchange=exchange, exchange_type='fanout', durable=True)

        # Publish message to the exchange
        channel.basic_publish(
            exchange=exchange,
            routing_key='',  # Ignored for fanout exchanges
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )

        connection.close()
        return True
    except AMQPError as e:
        print(f"Failed to publish to RabbitMQ exchange: {e}")
        return False

# Create a subscriber with a unique queue bound to the exchange
def create_subscriber(subscriber_id: Optional[str] = None, exchange: str = RABBITMQ_PUBSUB_EXCHANGE) -> str:
    """
    Create a subscriber with a unique queue bound to the exchange.
    
    Args:
        subscriber_id: An optional ID for the subscriber. If not provided, a random UUID will be generated.
        exchange: The name of the exchange to bind to (default: RABBITMQ_PUBSUB_EXCHANGE)
        
    Returns:
        str: The subscriber ID
    """
    if subscriber_id is None:
        subscriber_id = str(uuid.uuid4())
    
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
        )
        channel = connection.channel()

        # Declare a fanout exchange
        channel.exchange_declare(exchange=exchange, exchange_type='fanout', durable=True)

        # Create a queue with the subscriber ID
        queue_name = f"{RABBITMQ_PUBSUB_QUEUE_PREFIX}-{subscriber_id}"
        
        # Declare a queue with auto-delete=True so it's removed when the consumer disconnects
        channel.queue_declare(queue=queue_name, exclusive=True, auto_delete=True)
        
        # Bind the queue to the exchange
        channel.queue_bind(exchange=exchange, queue=queue_name)
        
        connection.close()
        
        # Initialize the message list for this subscriber
        pubsub_messages[subscriber_id] = []
        
        return subscriber_id
    except AMQPError as e:
        print(f"Failed to create subscriber: {e}")
        return None

# RabbitMQ Consumer for Pub/Sub pattern
def consume_as_subscriber(subscriber_id: str, background_tasks: BackgroundTasks, exchange: str = RABBITMQ_PUBSUB_EXCHANGE):
    """
    Consume messages as a subscriber.
    
    Args:
        subscriber_id: The ID of the subscriber
        background_tasks: FastAPI BackgroundTasks object
        exchange: The name of the exchange to consume from (default: RABBITMQ_PUBSUB_EXCHANGE)
    """
    def callback(ch, method, properties, body):
        message = json.loads(body)
        # Add the message to the subscriber's message list
        if subscriber_id in pubsub_messages:
            pubsub_messages[subscriber_id].append(message)
        print(f"Subscriber {subscriber_id} received message: {message}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def consume():
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
            )
            channel = connection.channel()

            # Declare a fanout exchange
            channel.exchange_declare(exchange=exchange, exchange_type='fanout', durable=True)

            # Get the queue name for this subscriber
            queue_name = f"{RABBITMQ_PUBSUB_QUEUE_PREFIX}-{subscriber_id}"
            
            # Declare a queue with auto-delete=True so it's removed when the consumer disconnects
            result = channel.queue_declare(queue=queue_name, exclusive=True, auto_delete=True)
            
            # Bind the queue to the exchange
            channel.queue_bind(exchange=exchange, queue=queue_name)
            
            # Start consuming
            channel.basic_consume(queue=queue_name, on_message_callback=callback)
            
            print(f"Subscriber {subscriber_id} started. Waiting for messages...")
            channel.start_consuming()
        except AMQPError as e:
            print(f"Subscriber {subscriber_id} error: {e}")

    background_tasks.add_task(consume)
    return subscriber_id

# Get messages for a specific subscriber
def get_subscriber_messages(subscriber_id: str) -> List[Dict[str, Any]]:
    """
    Get all messages received by a specific subscriber.
    
    Args:
        subscriber_id: The ID of the subscriber
        
    Returns:
        List[Dict[str, Any]]: A list of messages received by the subscriber
    """
    return pubsub_messages.get(subscriber_id, [])