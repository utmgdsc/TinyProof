from argparse import ArgumentParser, Namespace
import asyncio
import logging
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

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


@app.get("/proofs")
async def get_proofs():
    lean_dir = Path("./")
    if not lean_dir.exists():
        return {"proofs": ["-- Error: Lean proof directory not found."]}

    lean_files = list(lean_dir.glob("*.lean"))
    if not lean_files:
        return {"proofs": ["-- Error: No Lean files found."]}

    proofs = []
    for file in lean_files:
        try:
            content = file.read_text()
            proofs.append(content)
        except Exception as e:
            proofs.append(f"-- Error reading file {file.name}: {e}")

    return {"proofs": proofs}


PROOF_STATES: list[str] = [
    "Proof State 1",
    "Proof State 2",
    "Proof State 3",
    "Proof State 4",
    "Proof State 5",
]


@app.websocket("/ws")
async def proof_solver_websocket(websocket: WebSocket):
    logging.info("[WebSocket] connection attempt")

    try:
        await websocket.accept()
    except Exception as e:
        logging.error(f"[WebSocket] Error: {e}")
        raise e

    logging.info("[WebSocket] connection established")

    try:
        # Send each proof state
        for proof_state in PROOF_STATES:
            # wait for a random time
            await asyncio.sleep(random.uniform(2, 4.5))
            await websocket.send_text(proof_state)

        # Send completion message
        await asyncio.sleep(random.uniform(2, 4.5))
        await websocket.send_text("PROOF_COMPLETE")

    except WebSocketDisconnect:
        logging.info("[WebSocket] disconnected")
    except Exception as e:
        logging.error(f"[WebSocket] Error: {e}")
        raise e
