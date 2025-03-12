from argparse import ArgumentParser, Namespace
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(dependencies=[])


@app.get("/")
async def root():
    return {"message": "World"}


@app.websocket("/ws")
async def proof_solver_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for proof solver, this endpoint is used to solve the proof and communicate with the client.
    """
    logging.info("[WebSocket] connection attempt")

    try:
        await websocket.accept()
    except Exception as e:
        logging.error(f"[WebSocket] Error: {e}")
        raise e

    logging.info("[WebSocket] connection established")

    try:
        while True:
            await websocket.send("Hello!")
            # sleep for 1 second
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logging.info("[WebSocket] disconnected")
    except Exception as e:
        logging.error(f"[WebSocket] Error: {e}")
        raise e
