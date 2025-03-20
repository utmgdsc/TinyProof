from argparse import ArgumentParser, Namespace
import uvicorn
import os
import subprocess

# Importing app here makes the syntax cleaner as it will be picked up by refactors
from app import app

def kill_port(port):
    try:
        result = subprocess.run(["lsof", "-ti", f"tcp:{port}"], capture_output=True, text=True)
        for pid in result.stdout.strip().split("\n"):
            if pid:
                print(f"Killing process on port {port}: PID {pid}")
                os.kill(int(pid), 9)
    except Exception as e:
        print(f"Could not kill process on port {port}: {e}")

if __name__ == "__main__":
    parser = ArgumentParser(description="Run the TinyProof backend server.")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the backend on.")
    parser.add_argument("--dev", action="store_true", help="Run the server in development mode.")

    args: Namespace = parser.parse_args()

    kill_port(args.port)

    uvicorn.run("start:app", host="0.0.0.0", port=args.port, reload=args.dev)
