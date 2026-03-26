#!/bin/bash

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start the FastAPI server
echo "Starting FastAPI server on http://localhost:8000..."
uvicorn backend.main:app --reload --port 8000
