from argparse import ArgumentParser, Namespace
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

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

mock_proofs = [
    "theorem add_zero (n : ℕ) : n + 0 = n :=\nbegin\n  rw add_zero\nend",
    "theorem zero_add (n : ℕ) : 0 + n = n :=\nbegin\n  rw zero_add\nend",
    "theorem and_comm (a b : Prop) : a ∧ b ↔ b ∧ a :=\nbegin\n  exact and_comm a b\nend",
]

@app.get("/proofs")
async def get_proofs():
    return {"proofs": mock_proofs}


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