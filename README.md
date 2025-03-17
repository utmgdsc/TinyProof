# TinyProof

## Running the App

### Development (with hot reload)

To start both the frontend and backend in development mode (using `Dockerfile.dev` and hot reloading):

```bash
docker-compose -f docker-compose.dev.yml up --build
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
docker-compose down
```

### Rebuild and start containers

```bash
docker-compose up --build
```

### Tail logs from all services

```bash
docker-compose logs -f
```
