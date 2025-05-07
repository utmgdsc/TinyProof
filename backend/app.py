# app.py
import os
os.environ["TRANSFORMERS_NO_CACHING_ALLOCATOR_WARMUP"] = "1"

import asyncio
import logging
import torch
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from transformers import AutoModelForCausalLM, AutoTokenizer
from contextlib import asynccontextmanager

from solver.dummy import NotAVerifier
from solver.rmaxts import RMaxTS

# ─── Lifespan handler (startup & shutdown) ────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load model + tokenizer onto GPU/MPS
    logging.info(f"CUDA available: {torch.cuda.is_available()}, GPUs: {torch.cuda.device_count()}")
    MODEL_NAME = "deepseek-ai/DeepSeek-Prover-V1.5-RL"

    logging.info("Loading tokenizer…")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    logging.info("Loading model…")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        device_map="auto",                # let it place submodules
        torch_dtype=torch.float16,        # half-precision everywhere
        low_cpu_mem_usage=True,           # stream weights from disk
        max_memory={                      # caps how much goes on each device
            "cpu": "30GB",                # plenty of RAM to hold most of it
            "mps": "8GB"                  # fits within MPS pool
        },
        offload_folder="offload",         # temporary caches CPU‐offloaded tensors here
    )
    logging.info("Model loaded.")

    logging.info("Initializing RMaxTS…")
    verifier = NotAVerifier()
    rmax_ts = RMaxTS(model=model, tokenizer=tokenizer, verifier=verifier)
    logging.info("RMaxTS ready.")

    # Attach to app.state for endpoints to use
    app.state.tokenizer = tokenizer
    app.state.rmax_ts = rmax_ts

    yield
    logging.info("⚙️ Shutting down DeepSeek server")


# ─── Create FastAPI app with our lifespan ─────────────────────────────────────
app = FastAPI(lifespan=lifespan)

# ─── CORS (allow all for now) ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "TinyProof backend up and running."}


@app.websocket("/ws")
async def proof_solver_websocket(websocket: WebSocket):
    print(1)
    logging.info("[WebSocket] connection attempt")
    await websocket.accept()
    print(2)
    logging.info("[WebSocket] connection established")

    try:
        # 1) Receive the user’s theorem
        theorem = await websocket.receive_text()
        print(3)
        logging.info(f"[WebSocket] received theorem: {theorem[:80]}…")

        # 2) Offload proof generation so we don’t block FastAPI
        loop = asyncio.get_event_loop()
        print(3.5)
        steps = await loop.run_in_executor(
            None,
            lambda: list (websocket.app.state.rmax_ts.generate_whole_proof(theorem))
        )
        print(steps)

        # 3) Stream each step back
        for step in steps:
            print("Step:" + step)
            logging.info(f"[WebSocket] sending step: {step[:80]}…")
            await websocket.send_text(step)
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        logging.info("[WebSocket] client disconnected")

    except Exception as e:
        logging.exception("[WebSocket] error during proof generation")
        await websocket.send_text(f"[Error] {e}")

    finally:
        await websocket.close()
        logging.info("[WebSocket] connection closed")