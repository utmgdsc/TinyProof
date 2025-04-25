import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from solver.dummy import NotAVerifier
from solver.rmaxts import RMaxTS

print('Before transformers')
print('After transformers')

app = FastAPI(dependencies=[])

# So frontend can fetch from backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock this down if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


print("CUDA available:", torch.cuda.is_available())
print("Number of GPUs:", torch.cuda.device_count())

# load model
print('a')
model_name = "deepseek-ai/DeepSeek-Prover-V1.5-RL"
print('b')
tokenizer = AutoTokenizer.from_pretrained(model_name)
print('c')
model = AutoModelForCausalLM.from_pretrained(
    model_name, device_map="auto",
    torch_dtype=torch.float16,    # half-precision
    low_cpu_mem_usage=True,       # streams weights, lowers RAM spike
    load_in_8bit=True             # if you’ve installed bitsandbytes
)
print('d')


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
        theorem_raw = await websocket.receive_text()  # USERS TYPED OUT THEOREM
        theorem: str = str(theorem_raw)
        logging.info(f"[WebSocket] received theorem: {theorem[:80]}…")

        verifier = NotAVerifier()

        rmax_ts = RMaxTS(model=model, tokenizer=tokenizer, verifier=verifier)

        # just get the next tactic
        best_tactic = rmax_ts.search_best_tactic(
            initial_state=theorem, num_iterations=100
        )

        print(f"Best tactic: {best_tactic}")

        for step in rmax_ts.generate_whole_proof(theorem=theorem):
            logging.info(f"[WebSocket] sending step: {step[:80]}…")
            await websocket.send_text(step)

        # Uncomment the block below to use the do_work function instead of generate_whole_proof

        # for response in do_work("example (a b c : Nat): c + a + b = a + (b + c) := by"):
        #     logging.info(f"[WebSocket] sending response: {response}")
        #     await websocket.send_text(response)
        #     await asyncio.sleep(randint(1, 3))

    except WebSocketDisconnect:
        logging.info("[WebSocket] disconnected")
    except Exception as e:
        logging.error(f"[WebSocket] Error: {e}")
        raise e

    await websocket.close()
