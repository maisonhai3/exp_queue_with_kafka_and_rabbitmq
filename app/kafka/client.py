import json

from fastapi import BackgroundTasks
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

from app.common.storage import kafka_messages
from app.kafka.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC


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
