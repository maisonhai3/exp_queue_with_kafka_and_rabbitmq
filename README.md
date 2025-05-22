# Queue Experiment Project

This is an experimental project to learn about message queues using both Kafka and RabbitMQ. The project provides a FastAPI application that demonstrates how to produce and consume messages with both queue systems.

## Overview

Message queues are a powerful way to decouple components in a distributed system. This project demonstrates two popular message queue technologies:

1. **Apache Kafka**: A distributed event streaming platform capable of handling trillions of events a day.
2. **RabbitMQ**: A message broker that implements the Advanced Message Queuing Protocol (AMQP).

## Prerequisites

- Python 3.7+
- Docker (for running Kafka and RabbitMQ)

## Setup

1. Clone this repository:
   ```
   git clone <repository-url>
   cd queue_exp
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Start Kafka and RabbitMQ using Docker:
   ```
   docker-compose up -d
   ```

   If you don't have a docker-compose.yml file, you can create one with the following content:
   ```yaml
   version: '3'
   services:
     zookeeper:
       image: confluentinc/cp-zookeeper:latest
       environment:
         ZOOKEEPER_CLIENT_PORT: 2181
         ZOOKEEPER_TICK_TIME: 2000
       ports:
         - "2181:2181"
       
     kafka:
       image: confluentinc/cp-kafka:latest
       depends_on:
         - zookeeper
       ports:
         - "9092:9092"
       environment:
         KAFKA_BROKER_ID: 1
         KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
         KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
         KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
       
     rabbitmq:
       image: rabbitmq:3-management
       ports:
         - "5672:5672"
         - "15672:15672"
   ```

4. Run the FastAPI application:
   ```
   uvicorn main:app --reload
   ```

## Usage

The API provides several endpoints to interact with Kafka and RabbitMQ:

### Kafka Operations

1. Send a message to Kafka:
   ```
   POST /kafka/send
   Content-Type: application/json
   
   {
     "message": "Hello Kafka!",
     "timestamp": "2023-01-01T12:00:00",
     "source": "test_client"
   }
   ```

2. Start consuming messages from Kafka:
   ```
   POST /kafka/consume
   ```

3. Get all received Kafka messages:
   ```
   GET /kafka/messages
   ```

### RabbitMQ Operations

1. Send a message to RabbitMQ:
   ```
   POST /rabbitmq/send
   Content-Type: application/json
   
   {
     "message": "Hello RabbitMQ!",
     "timestamp": "2023-01-01T12:00:00",
     "source": "test_client"
   }
   ```

2. Start consuming messages from RabbitMQ:
   ```
   POST /rabbitmq/consume
   ```

3. Get all received RabbitMQ messages:
   ```
   GET /rabbitmq/messages
   ```

## Understanding Message Queues

### Kafka vs RabbitMQ

| Feature | Kafka | RabbitMQ |
|---------|-------|----------|
| **Model** | Distributed log | Message broker |
| **Use Case** | High-throughput event streaming | Traditional message queuing |
| **Scalability** | Highly scalable | Moderately scalable |
| **Message Retention** | Can retain messages for a configurable time | Removes messages once consumed |
| **Ordering** | Guarantees order within a partition | FIFO within a queue |
| **Delivery Guarantee** | At-least-once (can be exactly-once with transactions) | At-least-once, at-most-once, exactly-once |

### Key Concepts

#### Kafka
- **Topic**: A category or feed name to which records are published
- **Partition**: Topics are divided into partitions for scalability
- **Producer**: Publishes messages to topics
- **Consumer**: Subscribes to topics and processes the feed of messages
- **Consumer Group**: Group of consumers that divides the work of consuming and processing records

#### RabbitMQ
- **Queue**: Buffer that stores messages
- **Exchange**: Receives messages from producers and pushes them to queues
- **Binding**: Link between a queue and an exchange
- **Producer**: Sends messages to an exchange
- **Consumer**: Receives messages from a queue

## Project Structure

- `main.py`: FastAPI application with Kafka and RabbitMQ integration
- `requirements.txt`: Project dependencies
- `test_main.http`: HTTP request examples for testing the API

## Learning Resources

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.