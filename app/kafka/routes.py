from typing import Dict, Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Body

from app.common.storage import kafka_messages
from app.kafka.client import get_kafka_producer, consume_kafka_messages
from app.kafka.config import KAFKA_TOPIC

router = APIRouter(prefix="/kafka", tags=["kafka"])

@router.post("/send")
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


@router.get("/messages")
async def get_kafka_messages_endpoint():
    """
    Get all messages received from Kafka.
    """
    return {"messages": kafka_messages}


@router.post("/consume")
async def start_kafka_consumer_endpoint(background_tasks: BackgroundTasks):
    """
    Start consuming messages from Kafka in the background.
    """
    consume_kafka_messages(background_tasks)
    return {"status": "success", "message": "Kafka consumer started"}
