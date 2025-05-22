from typing import Dict, Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Body, Path

from app.common.storage import rabbitmq_messages, task_results, pubsub_messages
from app.rabbitmq.client import publish_to_rabbitmq, consume_rabbitmq_messages
from app.rabbitmq.config import RABBITMQ_QUEUE, RABBITMQ_TASK_QUEUE, RABBITMQ_PUBSUB_EXCHANGE
from app.rabbitmq.pubsub import publish_to_exchange, create_subscriber, consume_as_subscriber, get_subscriber_messages
from app.rabbitmq.tasks import publish_task, start_workers

router = APIRouter()

# RabbitMQ basic messaging routes
rabbitmq_router = APIRouter(prefix="/rabbitmq", tags=["rabbitmq"])

@rabbitmq_router.post("/send")
async def send_to_rabbitmq_endpoint(message: Dict[str, Any] = Body(...)):
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


@rabbitmq_router.get("/messages")
async def get_rabbitmq_messages_endpoint():
    """
    Get all messages received from RabbitMQ.
    """
    return {"messages": rabbitmq_messages}


@rabbitmq_router.post("/consume")
async def start_rabbitmq_consumer_endpoint(background_tasks: BackgroundTasks):
    """
    Start consuming messages from RabbitMQ in the background.
    """
    consume_rabbitmq_messages(background_tasks)
    return {"status": "success", "message": "RabbitMQ consumer started"}


# Task system routes
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])

@tasks_router.post("/submit")
async def submit_task_endpoint(task: Dict[str, Any] = Body(...)):
    """
    Submit a task to the RabbitMQ task queue.

    The task should be a JSON object with at least:
    - complexity: A number representing the task complexity (processing time)
    - data: Any data needed for the task
    """
    if 'complexity' not in task:
        raise HTTPException(status_code=400, detail="Task must include 'complexity' field")

    success = publish_task(task)
    if not success:
        raise HTTPException(status_code=503, detail="Failed to publish task to RabbitMQ")

    return {
        "status": "success",
        "message": "Task submitted to queue",
        "task_id": task.get('task_id'),
        "queue": RABBITMQ_TASK_QUEUE
    }


@tasks_router.post("/workers/start")
async def start_task_workers_endpoint(background_tasks: BackgroundTasks, num_workers: int = Body(3, embed=True)):
    """
    Start a specified number of worker consumers to process tasks from the queue.

    Default is 3 workers.
    """
    if num_workers < 1:
        raise HTTPException(status_code=400, detail="Number of workers must be at least 1")

    if num_workers > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 workers allowed")

    worker_ids = start_workers(num_workers, background_tasks)

    return {
        "status": "success",
        "message": f"Started {num_workers} workers",
        "worker_ids": worker_ids
    }


@tasks_router.get("/results")
async def get_task_results_endpoint():
    """
    Get all task processing results.
    """
    return {"results": task_results}

# Pub/Sub system routes
pubsub_router = APIRouter(prefix="/pubsub", tags=["pubsub"])

@pubsub_router.post("/publish")
async def publish_message_endpoint(message: Dict[str, Any] = Body(...)):
    """
    Publish a message to the RabbitMQ exchange using the Publish/Subscribe pattern.

    The message will be broadcast to all subscribers.
    """
    success = publish_to_exchange(message)
    if not success:
        raise HTTPException(status_code=503, detail="Failed to publish to RabbitMQ exchange")

    return {
        "status": "success",
        "message": "Message published to exchange",
        "exchange": RABBITMQ_PUBSUB_EXCHANGE
    }

@pubsub_router.post("/subscribers")
async def create_subscriber_endpoint(subscriber_id: Optional[str] = Body(None, embed=True)):
    """
    Create a new subscriber with a unique queue bound to the exchange.

    If subscriber_id is not provided, a random UUID will be generated.
    """
    subscriber_id = create_subscriber(subscriber_id)
    if not subscriber_id:
        raise HTTPException(status_code=503, detail="Failed to create subscriber")

    return {
        "status": "success",
        "message": "Subscriber created",
        "subscriber_id": subscriber_id
    }

@pubsub_router.post("/subscribers/{subscriber_id}/consume")
async def start_subscriber_consumer_endpoint(
    background_tasks: BackgroundTasks,
    subscriber_id: str = Path(..., description="The ID of the subscriber")
):
    """
    Start consuming messages as a subscriber.
    """
    if subscriber_id not in pubsub_messages:
        # Create the subscriber if it doesn't exist
        create_subscriber(subscriber_id)

    consume_as_subscriber(subscriber_id, background_tasks)

    return {
        "status": "success",
        "message": f"Subscriber {subscriber_id} started consuming messages",
        "exchange": RABBITMQ_PUBSUB_EXCHANGE
    }

@pubsub_router.get("/subscribers/{subscriber_id}/messages")
async def get_subscriber_messages_endpoint(
    subscriber_id: str = Path(..., description="The ID of the subscriber")
):
    """
    Get all messages received by a specific subscriber.
    """
    if subscriber_id not in pubsub_messages:
        raise HTTPException(status_code=404, detail=f"Subscriber {subscriber_id} not found")

    return {
        "subscriber_id": subscriber_id,
        "messages": get_subscriber_messages(subscriber_id)
    }

@pubsub_router.get("/subscribers")
async def get_all_subscribers_endpoint():
    """
    Get a list of all subscribers.
    """
    return {
        "subscribers": list(pubsub_messages.keys())
    }

# Add all routers to the main router
router.include_router(rabbitmq_router)
router.include_router(tasks_router)
router.include_router(pubsub_router)
