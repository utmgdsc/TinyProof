from argparse import ArgumentParser, Namespace
import uvicorn

# Importing app here makes the syntax cleaner as it will be picked up by refactors
from app import app

if __name__ == "__main__":
    parser = ArgumentParser(description="Run the TinyProof backend server.")
    parser.add_argument("--port", type=int, default=5050, help="Port to run the backend on.")
    parser.add_argument("--dev", action="store_true", help="Run the server in development mode.")

    args: Namespace = parser.parse_args()

    uvicorn.run("start:app", host="0.0.0.0", port=args.port, reload=args.dev)
