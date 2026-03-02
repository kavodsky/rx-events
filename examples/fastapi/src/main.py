from fastapi import FastAPI
from contextlib import asynccontextmanager

# Import your API router
from src.endpoints import router
from rx_events import event_bus

# Import DS processors module (will be initialized after channels are created)
from src.data_science.processors import DataScienceProcessors


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle with proper channel setup"""

    # Initialize event channels with different configurations
    event_bus.create_ack_channel(
        "user_analysis",
        allow_duplicates=False,
        timeout_seconds=180  # 3 minutes for complex ML
    )

    event_bus.create_ack_channel(
        "recommendations",
        allow_duplicates=False,
        timeout_seconds=300  # 5 minutes for heavy processing
    )

    event_bus.create_ack_channel(
        "analytics",
        allow_duplicates=True,
        timeout_seconds=60  # 1 minute for quick analytics
    )

    # Initialize DS processors after channels are created (they auto-register)
    ds_processors = DataScienceProcessors()

    print("🚀 Event bus initialized with acknowledgment channels")
    print("🧠 DS processors registered and listening")
    print("✅ Application ready - events will be tracked with acks")

    yield

    print("🛑 Application shutting down")


# Create main FastAPI app
app = FastAPI(
    title="Event-Driven API with Acknowledgments",
    description="API publishes events, DS processes them, sends acknowledgments back",
    lifespan=lifespan
)

# Include API routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)