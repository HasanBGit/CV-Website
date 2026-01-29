#!/bin/bash

# Build and run the CV Generator
echo "Building CV Generator..."
docker-compose build

echo "Starting CV Generator..."
docker-compose up

echo "CV Generator is running at http://localhost:5000"
