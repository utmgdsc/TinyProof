import uvicorn
from fastapi import FastAPI

app = FastAPI(dependencies=[])


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(app, port=5000)
