import asyncio
import logging
from random import randint
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from solver.mcts_test import do_work

app = FastAPI(dependencies=[])

# So frontend can fetch from backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock this down if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        for response in do_work("example (a b c : Nat): c + a + b = a + (b + c) := by"):
            logging.info(f"[WebSocket] sending response: {response}")
            await websocket.send_text(response)
            await asyncio.sleep(randint(1, 3))

    except WebSocketDisconnect:
        logging.info("[WebSocket] disconnected")
    except Exception as e:
        logging.error(f"[WebSocket] Error: {e}")
        raise e

    await websocket.close()
