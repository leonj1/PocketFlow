FROM python:3.9-slim

WORKDIR /app

# Copy the entire PocketFlow repository
COPY . /app/

# Install dependencies and PocketFlow in development mode
RUN pip install --no-cache-dir -e .

# Install doc-generator specific requirements
RUN pip install --no-cache-dir -r /app/cookbook/doc-generator/requirements.txt

# Set the working directory to doc-generator
WORKDIR /app/cookbook/doc-generator

# Run the script
CMD ["python", "main.py"]
