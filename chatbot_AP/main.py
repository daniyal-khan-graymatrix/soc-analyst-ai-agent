# main.py

from fastapi import FastAPI
from chat_api import router as chat_stream_router  # your SSE chat route

app = FastAPI(
    title="SOC Analyst AI Agent",
    description="Real-time SOC Assistant using FastAPI + LangGraph",
    version="1.0.0",
)

# Register routers
app.include_router(chat_stream_router)

# Optionally add healthcheck route
@app.get("/ping")
def ping():
    return {"status": "ok"}

# Only needed if you want to run using `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
