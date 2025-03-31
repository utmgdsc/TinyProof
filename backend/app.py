from argparse import ArgumentParser, Namespace
import asyncio
import logging
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
        while True:
            # Step 1: Receive Lean statement from client
            data = await websocket.receive_text()
            logging.info(f"Received Lean statement: {data}")

            # Step 2: CALL MODEL HERE
            # In real use, send `data` to model
            # For now, just mock a proof result
            generated_proof = f"theorem result : {data} :=\nbegin\n  exact proof_goes_here\nend"

            # Step 3: Send proof back to frontend
            await websocket.send_text(generated_proof)
    except WebSocketDisconnect:
        logging.info("[WebSocket] disconnected")
    except Exception as e:
        logging.error(f"[WebSocket] Error: {e}")
        raise e