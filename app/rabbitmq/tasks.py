import json
import random
import time
import uuid
from typing import Dict, Any, List

import pika
from fastapi import BackgroundTasks
from pika.exceptions import AMQPError

from app.common.storage import task_results
from app.rabbitmq.client import publish_to_rabbitmq
from app.rabbitmq.config import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_TASK_QUEUE


# Task Producer
def publish_task(task: Dict[str, Any]) -> bool:
    """
    Publish a task to the RabbitMQ task queue.

    The task should be a JSON object with at least:
    - task_id: A unique identifier for the task
    - complexity: A number representing the task complexity (processing time)
    """
    task_with_id = task.copy()
    if 'task_id' not in task_with_id:
        task_with_id['task_id'] = str(uuid.uuid4())

    return publish_to_rabbitmq(task_with_id, RABBITMQ_TASK_QUEUE)

# Worker Consumer
def start_worker(worker_id: str, background_tasks: BackgroundTasks):
    def process_task(ch, method, properties, body):
        task = json.loads(body)
        print(f"Worker {worker_id} received task: {task}")

        # Simulate work based on task complexity
        complexity = task.get('complexity', 1)
        # Add some randomness to simulate varying processing times
        processing_time = complexity * (0.5 + random.random())

        # Simulate processing
        time.sleep(processing_time)

        # Create result
        result = {
            'task_id': task.get('task_id', 'unknown'),
            'worker_id': worker_id,
            'input': task,
            'processing_time': processing_time,
            'completed_at': time.time(),
            'status': 'completed'
        }

        # Store result
        task_results.append(result)

        print(f"Worker {worker_id} completed task {task.get('task_id', 'unknown')} in {processing_time:.2f} seconds")

        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def consume():
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
            )
            channel = connection.channel()

            channel.queue_declare(queue=RABBITMQ_TASK_QUEUE, durable=True)
            # Fair dispatch - don't give more than one message to a worker at a time
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=RABBITMQ_TASK_QUEUE, on_message_callback=process_task)

            print(f"Worker {worker_id} started. Waiting for tasks...")
            channel.start_consuming()
        except AMQPError as e:
            print(f"Worker {worker_id} error: {e}")

    background_tasks.add_task(consume)
    return worker_id

# Start multiple workers
def start_workers(num_workers: int, background_tasks: BackgroundTasks) -> List[str]:
    worker_ids = []
    for i in range(num_workers):
        worker_id = f"worker-{i+1}"
        start_worker(worker_id, background_tasks)
        worker_ids.append(worker_id)
    return worker_ids
