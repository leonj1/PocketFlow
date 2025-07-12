# Docker Setup for PocketFlow Document Workflow

This guide explains how to run the PocketFlow document workflow implementation using Docker.

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t pocketflow-document-workflow .
```

### 2. Run the Workflow

**Interactive mode (recommended for the workflow):**
```bash
docker run -it --rm pocketflow-document-workflow
```

**With persistent output:**
```bash
docker run -it --rm \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/archive:/app/archive \
  -v $(pwd)/published:/app/published \
  pocketflow-document-workflow
```

## Using Docker Compose

### Basic Usage

```bash
# Run the workflow
docker-compose run --rm document-workflow

# Run tests
docker-compose run --rm document-workflow test

# Development mode with shell
docker-compose --profile dev run --rm document-workflow-dev
```

### Build and Run

```bash
# Build the image
docker-compose build

# Run with auto-remove
docker-compose run --rm document-workflow

# Run in background (not recommended for interactive workflow)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop and remove
docker-compose down
```

## Available Commands

The container supports multiple commands through the entrypoint script:

- `workflow` - Run the main document workflow (default)
- `test` - Run the test suite
- `shell` - Start an interactive Python shell with modules loaded
- `bash` - Start a bash shell
- `custom <file>` - Run a custom Python workflow file
- `help` - Show help message

### Examples

```bash
# Run tests
docker run -it --rm pocketflow-document-workflow test

# Interactive Python shell
docker run -it --rm pocketflow-document-workflow shell

# Run custom workflow
docker run -it --rm \
  -v $(pwd)/my_workflow.py:/app/my_workflow.py \
  pocketflow-document-workflow custom my_workflow.py

# Direct Python command
docker run -it --rm pocketflow-document-workflow -c "print('Hello from PocketFlow')"
```

## Customizing Context

### Using a Custom context.yml

```bash
# Mount your custom context file
docker run -it --rm \
  -v $(pwd)/my_context.yml:/app/context.yml \
  pocketflow-document-workflow
```

### With Docker Compose

Edit the `docker-compose.yml` to mount your context:

```yaml
volumes:
  - ./my_context.yml:/app/context.yml
```

## Volume Mounts

The container creates these directories for output:

- `/app/output` - General output files
- `/app/archive` - Archived documents
- `/app/published` - Published documents

Mount these as volumes to persist data:

```bash
docker run -it --rm \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/archive:/app/archive \
  -v $(pwd)/published:/app/published \
  pocketflow-document-workflow
```

## Development Mode

For development with live code reloading:

```bash
# Using docker-compose (recommended)
docker-compose --profile dev run --rm document-workflow-dev

# Or manually
docker run -it --rm \
  -v $(pwd):/app \
  --entrypoint /bin/bash \
  pocketflow-document-workflow
```

## Environment Variables

- `PYTHONUNBUFFERED=1` - Ensures output is displayed immediately
- `WORKFLOW_ENV=docker` - Indicates running in Docker environment

## Resource Limits

The docker-compose.yml includes optional resource limits:

- CPU: 1 core limit, 0.5 core reservation
- Memory: 512MB limit, 256MB reservation

Adjust these in `docker-compose.yml` as needed.

## Troubleshooting

### Permission Issues

If you encounter permission errors with output directories:

```bash
# Create directories with correct permissions
mkdir -p output archive published
chmod 777 output archive published
```

### Interactive Input Not Working

Ensure you're using the `-it` flags:
- `-i` - Keep STDIN open
- `-t` - Allocate a pseudo-TTY

### Can't Find context.yml

The default context.yml must be in the build context. Either:
1. Ensure context.yml exists in the current directory
2. Mount your own: `-v $(pwd)/my_context.yml:/app/context.yml`

## Building for Production

For a production build with specific tags:

```bash
# Build with version tag
docker build -t pocketflow-document-workflow:1.0.0 -t pocketflow-document-workflow:latest .

# Push to registry
docker tag pocketflow-document-workflow:latest myregistry/pocketflow-document-workflow:latest
docker push myregistry/pocketflow-document-workflow:latest
```

## Security Notes

- Runs as non-root user (uid 1000)
- No unnecessary system packages installed
- Python dependencies pinned to specific versions
- Output directories created with restricted permissions