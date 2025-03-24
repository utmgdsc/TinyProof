# TinyProof

## Running the App

### Development (with hot reload)

To start both the frontend and backend in development mode (using `Dockerfile.dev` and hot reloading), ensure you have Docker Desktop downloaded and running on your machine and run:

```bash
docker-compose -f up --build
```

or

```bash
docker compose up
```

If you want to start the backend and frontend without using Docker (Lean Server will not work), the in one terminal, run

```bash
cd backend
python start.py --port 5000 --dev
```

and in another terminal, run

```bash
cd frontend
npm install
npm run dev
```

```bash
docker-compose -f up --build
```

## Useful Commands

### Stop all running containers

```bash
docker-compose -f down
```

### Rebuild and start containers

```bash
docker-compose up --build
```
