# TinyProof

## Running the App

### Development (with hot reload)

To start both the frontend and backend in development mode (using `Dockerfile.dev` and hot reloading), ensure you have Docker Desktop downloaded and running on your machine and run:

```bash
docker-compose -f docker-compose.dev.yml up --build
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

## Production

To start the app in production mode:

```bash
docker-compose -f docker-compose.prod.yml up --build
```

## Project Structure

```bash
.
├── backend/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── ...
├── frontend/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── ...
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── README.md
```

## Useful Commands

### Stop all running containers

```bash
docker-compose -f docker-compose.dev.yml down
```

or

```bash
docker-compose -f docker-compose.prod.yml down
```

### Rebuild and start containers

```bash
docker-compose up --build
```

### Tail logs from all services

```bash
docker-compose logs -f
```
