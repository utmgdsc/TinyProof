# Claude was used to help generate this Dockerfile

# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \ 
    git \
    && rm -rf /var/lib/apt/lists/*

# Install elan (Lean version manager)
RUN curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y
ENV PATH="/root/.elan/bin:${PATH}"

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --default-timeout=100 -r requirements.txt 

# Install torch with CUDA 11.8 support
RUN pip install torch --index-url https://download.pytorch.org/whl/cu118

RUN pip install accelerate

# Copy the rest of the application
COPY . .

# Default port
ENV PORT=8080

# Expose the port the app runs on
EXPOSE ${PORT}

# Command to run the application
CMD python -u start.py --port ${PORT}
