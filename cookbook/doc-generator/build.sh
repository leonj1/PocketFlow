#!/bin/bash

# Build the Docker image from the repository root
cd ../.. && docker build -t pocketflow-doc-generator -f cookbook/doc-generator/Dockerfile .