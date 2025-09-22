#!/bin/bash

echo "Starting Oceanographic Data Chatbot Backend..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not available"
    echo "Please ensure pip is installed with Python"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Check if installation was successful
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    echo "Please check your internet connection and try again"
    exit 1
fi

echo
echo "Dependencies installed successfully!"
echo "Starting FastAPI server on http://localhost:8000"
echo
echo "Press Ctrl+C to stop the server"
echo

# Start the FastAPI server
python3 main.py