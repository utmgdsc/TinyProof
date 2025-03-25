# TinyProof

## Running the App

Follow README in backend and frontend first. Then follow this README

### Development (with hot reload)

To start both the frontend and backend, ensure you have Docker Desktop downloaded and running on your machine and run:

```bash
docker-compose up --build
```

if you want to rebuild the images everytime to ensure latest images. If not, just run:

```bash
docker compose up
```

If using an ARM64 machine, add the following line below "frontend:" in the docker-compose.yml:

```compose
platform: linux/arm64
```

To rebuild clean, run

```bash
docker compose down -v --remove-orphans

rm -rf frontend/node_modules frontend/package-lock.json

docker compose build --no-cache

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
