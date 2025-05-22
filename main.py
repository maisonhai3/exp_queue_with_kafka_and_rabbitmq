from fastapi import FastAPI, APIRouter

# Import routers from modules
from app.kafka.routes import router as kafka_router
from app.rabbitmq.routes import router as rabbitmq_router

# Create FastAPI app
app = FastAPI(title="Queue Experiment", description="An experimental project to learn about Kafka and RabbitMQ")

# Create main router
main_router = APIRouter()

@main_router.get("/")
async def root():
    return {
        "message": "Queue Experiment API",
        "kafka_endpoint": "/kafka/send",
        "rabbitmq_endpoint": "/rabbitmq/send",
        "kafka_messages": "/kafka/messages",
        "rabbitmq_messages": "/rabbitmq/messages",
        "task_endpoints": {
            "submit_task": "/tasks/submit",
            "start_workers": "/tasks/workers/start",
            "get_results": "/tasks/results"
        }
    }


@main_router.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

# Include routers
app.include_router(main_router)
app.include_router(kafka_router)
app.include_router(rabbitmq_router)
