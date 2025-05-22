from fastapi import FastAPI, BackgroundTasks, HTTPException, Body
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Kafka imports
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

# RabbitMQ imports
import pika
from pika.exceptions import AMQPError

app = FastAPI(title="Queue Experiment", description="An experimental project to learn about Kafka and RabbitMQ")

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "test-topic")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "test-queue")

# In-memory message storage for demonstration purposes
kafka_messages = []
rabbitmq_messages = []

# Kafka Producer
def get_kafka_producer():
    try:
        return KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except KafkaError as e:
        print(f"Failed to create Kafka producer: {e}")
        return None

# Kafka Consumer
def consume_kafka_messages(background_tasks: BackgroundTasks):
    def consume():
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='queue-exp-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )

            for message in consumer:
                kafka_messages.append(message.value)
                print(f"Received Kafka message: {message.value}")

        except KafkaError as e:
            print(f"Kafka consumer error: {e}")

    background_tasks.add_task(consume)

# RabbitMQ Producer
def publish_to_rabbitmq(message: Dict[str, Any]) -> bool:
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
        )
        channel = connection.channel()

        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
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

@app.get("/")
async def root():
    return {
        "message": "Queue Experiment API",
        "kafka_endpoint": "/kafka/send",
        "rabbitmq_endpoint": "/rabbitmq/send",
        "kafka_messages": "/kafka/messages",
        "rabbitmq_messages": "/rabbitmq/messages"
    }


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


# Kafka endpoints
@app.post("/kafka/send")
async def send_to_kafka(message: Dict[str, Any] = Body(...)):
    """
    Send a message to Kafka.

    The message should be a JSON object.
    """
    producer = get_kafka_producer()
    if not producer:
        raise HTTPException(status_code=503, detail="Kafka producer not available")

    try:
        future = producer.send(KAFKA_TOPIC, message)
        result = future.get(timeout=60)
        producer.close()

        return {
            "status": "success",
            "message": "Message sent to Kafka",
            "topic": KAFKA_TOPIC,
            "partition": result.partition,
            "offset": result.offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message to Kafka: {str(e)}")


@app.get("/kafka/messages")
async def get_kafka_messages():
    """
    Get all messages received from Kafka.
    """
    return {"messages": kafka_messages}


@app.post("/kafka/consume")
async def start_kafka_consumer(background_tasks: BackgroundTasks):
    """
    Start consuming messages from Kafka in the background.
    """
    consume_kafka_messages(background_tasks)
    return {"status": "success", "message": "Kafka consumer started"}


# RabbitMQ endpoints
@app.post("/rabbitmq/send")
async def send_to_rabbitmq(message: Dict[str, Any] = Body(...)):
    """
    Send a message to RabbitMQ.

    The message should be a JSON object.
    """
    success = publish_to_rabbitmq(message)
    if not success:
        raise HTTPException(status_code=503, detail="Failed to publish to RabbitMQ")

    return {
        "status": "success",
        "message": "Message sent to RabbitMQ",
        "queue": RABBITMQ_QUEUE
    }


@app.get("/rabbitmq/messages")
async def get_rabbitmq_messages():
    """
    Get all messages received from RabbitMQ.
    """
    return {"messages": rabbitmq_messages}


@app.post("/rabbitmq/consume")
async def start_rabbitmq_consumer(background_tasks: BackgroundTasks):
    """
    Start consuming messages from RabbitMQ in the background.
    """
    consume_rabbitmq_messages(background_tasks)
    return {"status": "success", "message": "RabbitMQ consumer started"}
