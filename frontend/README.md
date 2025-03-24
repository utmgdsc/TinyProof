# Overview

This folder hosts the frontend for Tinyproof. This is an adaptation of [Lean4Web](https://github.com/leanprover-community/lean4web)

# Build Instructions

## Requirements

Ensure you have Docker and ensure that Docker daemon/Desktop is running.

You can check that Docker daemon/Docker Desktop is running by using:

```bash
docker info
```

## Build & Run

Build the Docker image using

```bash
cd frontend && docker build -t tinyproof-frontend .
```

(the build can take painfully long 😭)

Run the Docker image using

```bash
docker run -p 3000:3000 tinyproof-frontend
```

Note: `3000` represents the port the front-end and the Lean4 server will be running on.

## Development

If you want to play around with the front-end in development, the Lean server will not work unless you're running Linux.

But, to do so:

Install all required npm packages

```
npm install
```

Run the front-end server

```
npm start
```