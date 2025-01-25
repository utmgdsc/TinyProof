import uvicorn
from argparse import ArgumentParser, Namespace
from fastapi import FastAPI

app = FastAPI(dependencies=[])


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    parser = ArgumentParser(description="Run the TinyProof backend server.")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the backend on.")

    args: Namespace = parser.parse_args()

    port: int = args.port

    uvicorn.run(app, port=port)
