from argparse import ArgumentParser, Namespace
import asyncio
from fastapi import FastAPI, WebSocket

app = FastAPI(dependencies=[])

@app.get("/")

async def root():
    return {"message": "World"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("WebSocket connected")
    await websocket.accept()
    while True:
        await websocket.send_text(f"Hello!")
        # sleep for 1 second
        await asyncio.sleep(1)
