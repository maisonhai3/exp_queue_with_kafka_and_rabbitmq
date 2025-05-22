import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "test-topic")

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "test-queue")
RABBITMQ_TASK_QUEUE = os.getenv("RABBITMQ_TASK_QUEUE", "task-queue")
RABBITMQ_PUBSUB_EXCHANGE = os.getenv("RABBITMQ_PUBSUB_EXCHANGE", "pubsub-exchange")
RABBITMQ_PUBSUB_QUEUE_PREFIX = os.getenv("RABBITMQ_PUBSUB_QUEUE_PREFIX", "pubsub-queue")
