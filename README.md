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

### RabbitMQ Workload Distribution

This project also demonstrates how RabbitMQ can be used to distribute workload among multiple workers. This is a common use case for message queues in distributed systems.

1. Start worker consumers (default 3 workers):
   ```
   POST /tasks/workers/start
   Content-Type: application/json

   {
     "num_workers": 3
   }
   ```

2. Submit tasks with different complexity levels:
   ```
   POST /tasks/submit
   Content-Type: application/json

   {
     "complexity": 3,
     "data": "This is a task that needs processing",
     "type": "analysis"
   }
   ```

   The `complexity` field determines how long the task will take to process (higher values mean longer processing times).

3. Get all task results:
   ```
   GET /tasks/results
   ```

   This will show which worker processed each task and how long it took.

#### How Workload Distribution Works

1. **Task Queue**: Tasks are sent to a dedicated RabbitMQ queue.
2. **Multiple Workers**: Multiple worker consumers process tasks from the queue.
3. **Fair Dispatch**: RabbitMQ uses a round-robin algorithm to distribute tasks, but with the `prefetch_count=1` setting, it won't give a new task to a worker until it has finished its current task.
4. **Acknowledgments**: Workers acknowledge tasks only after they've been processed, ensuring that if a worker crashes, the task will be reassigned to another worker.

This demonstrates how RabbitMQ can be used to distribute work among multiple consumers, allowing for parallel processing and improved throughput.

### RabbitMQ Publish/Subscribe

This project also demonstrates the Publish/Subscribe pattern using RabbitMQ exchanges and bindings. This pattern allows a message to be broadcast to multiple consumers.

1. Create a subscriber:
   ```
   POST /pubsub/subscribers
   Content-Type: application/json

   {
     "subscriber_id": "subscriber-1"
   }
   ```

   If `subscriber_id` is not provided, a random UUID will be generated.

2. Start a subscriber consumer:
   ```
   POST /pubsub/subscribers/subscriber-1/consume
   ```

3. Publish a message to all subscribers:
   ```
   POST /pubsub/publish
   Content-Type: application/json

   {
     "message": "Hello Subscribers!",
     "timestamp": "2023-01-01T12:00:00",
     "source": "test_client",
     "importance": "high"
   }
   ```

4. Get messages for a specific subscriber:
   ```
   GET /pubsub/subscribers/subscriber-1/messages
   ```

5. Get all subscribers:
   ```
   GET /pubsub/subscribers
   ```

#### How Publish/Subscribe Works

1. **Exchange**: Messages are sent to an exchange instead of directly to a queue.
2. **Fanout Exchange**: A fanout exchange broadcasts all messages it receives to all queues bound to it.
3. **Queue Binding**: Each subscriber has a unique queue that is bound to the exchange.
4. **Message Broadcast**: When a message is published to the exchange, it is delivered to all bound queues.
5. **Subscriber Consumption**: Each subscriber consumes messages from its own queue.

This demonstrates how RabbitMQ can be used to implement the Publish/Subscribe pattern, allowing a message to be broadcast to multiple consumers.

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

- `main.py`: Main FastAPI application that imports and uses the modules
- `app/`: Directory containing the application code
  - `common/`: Common utilities and configuration
    - `config.py`: Shared configuration loaded from environment variables
    - `storage.py`: In-memory message storage
  - `kafka/`: Kafka-related functionality
    - `config.py`: Kafka-specific configuration
    - `client.py`: Kafka producer and consumer implementation
    - `routes.py`: Kafka API endpoints
  - `rabbitmq/`: RabbitMQ-related functionality
    - `config.py`: RabbitMQ-specific configuration
    - `client.py`: RabbitMQ producer and consumer implementation
    - `tasks.py`: RabbitMQ task system for workload distribution
    - `pubsub.py`: RabbitMQ publish/subscribe implementation with exchanges and bindings
    - `routes.py`: RabbitMQ API endpoints
- `requirements.txt`: Project dependencies
- `test_main.http`: HTTP request examples for testing the API
- `docker-compose.yml`: Docker configuration for running Kafka and RabbitMQ

## Learning Resources

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
