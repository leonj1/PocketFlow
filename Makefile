# Makefile for PocketFlow Document Workflow

# Variables
IMAGE_NAME := pocketflow-document-workflow
IMAGE_TAG := latest
CONTAINER_NAME := document_workflow
DOCKER := docker
DOCKER_COMPOSE := docker-compose

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# Phony targets
.PHONY: build run test shell clean help dev logs stop push pull lint check

# Build the Docker image
build:
	@echo "$(GREEN)Building Docker image: $(IMAGE_NAME):$(IMAGE_TAG)$(NC)"
	$(DOCKER) build -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "$(GREEN)Build complete!$(NC)"

# Run the workflow interactively
run:
	@echo "$(GREEN)Running document workflow...$(NC)"
	$(DOCKER) run -it --rm \
		--name $(CONTAINER_NAME) \
		-v $(PWD)/output:/app/output \
		-v $(PWD)/archive:/app/archive \
		-v $(PWD)/published:/app/published \
		$(IMAGE_NAME):$(IMAGE_TAG)

# Run tests
test:
	@echo "$(GREEN)Running tests...$(NC)"
	$(DOCKER) run -it --rm \
		--name $(CONTAINER_NAME)_test \
		$(IMAGE_NAME):$(IMAGE_TAG) test

# Open interactive Python shell
shell:
	@echo "$(GREEN)Starting interactive Python shell...$(NC)"
	$(DOCKER) run -it --rm \
		--name $(CONTAINER_NAME)_shell \
		$(IMAGE_NAME):$(IMAGE_TAG) shell

# Open bash shell for development
bash:
	@echo "$(GREEN)Starting bash shell...$(NC)"
	$(DOCKER) run -it --rm \
		--name $(CONTAINER_NAME)_bash \
		-v $(PWD):/app \
		$(IMAGE_NAME):$(IMAGE_TAG) bash

# Development mode with docker-compose
dev:
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) --profile dev run --rm document-workflow-dev

# Build using docker-compose
compose-build:
	@echo "$(GREEN)Building with docker-compose...$(NC)"
	$(DOCKER_COMPOSE) build

# Run using docker-compose
compose-run:
	@echo "$(GREEN)Running with docker-compose...$(NC)"
	$(DOCKER_COMPOSE) run --rm document-workflow

# View logs
logs:
	$(DOCKER_COMPOSE) logs -f

# Stop all containers
stop:
	@echo "$(YELLOW)Stopping containers...$(NC)"
	$(DOCKER_COMPOSE) down

# Clean up Docker resources
clean:
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) down -v --rmi local
	$(DOCKER) rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

# Remove output directories
clean-output:
	@echo "$(YELLOW)Cleaning output directories...$(NC)"
	rm -rf output/ archive/ published/ audit_trail_*.json
	@echo "$(GREEN)Output directories cleaned!$(NC)"

# Full clean (Docker + outputs)
clean-all: clean clean-output

# Push image to registry
push:
	@echo "$(GREEN)Pushing image to registry...$(NC)"
	$(DOCKER) push $(IMAGE_NAME):$(IMAGE_TAG)

# Pull image from registry
pull:
	@echo "$(GREEN)Pulling image from registry...$(NC)"
	$(DOCKER) pull $(IMAGE_NAME):$(IMAGE_TAG)

# Lint Python code
lint:
	@echo "$(GREEN)Linting Python code...$(NC)"
	$(DOCKER) run --rm \
		-v $(PWD):/app \
		$(IMAGE_NAME):$(IMAGE_TAG) \
		-m pylint document_workflow.py || true

# Check if everything is ready
check:
	@echo "$(GREEN)Checking prerequisites...$(NC)"
	@which docker > /dev/null || (echo "$(RED)Docker not found!$(NC)" && exit 1)
	@which docker-compose > /dev/null || (echo "$(YELLOW)docker-compose not found (optional)$(NC)")
	@test -f context.yml || (echo "$(RED)context.yml not found!$(NC)" && exit 1)
	@test -f document_workflow.py || (echo "$(RED)document_workflow.py not found!$(NC)" && exit 1)
	@echo "$(GREEN)All prerequisites satisfied!$(NC)"

# Create output directories
init-dirs:
	@echo "$(GREEN)Creating output directories...$(NC)"
	mkdir -p output archive published
	@echo "$(GREEN)Directories created!$(NC)"

# Run with custom context
run-custom:
	@echo "$(GREEN)Running with custom context...$(NC)"
	@echo "$(YELLOW)Usage: make run-custom CONTEXT=my_context.yml$(NC)"
	$(DOCKER) run -it --rm \
		--name $(CONTAINER_NAME) \
		-v $(PWD)/$(CONTEXT):/app/context.yml \
		-v $(PWD)/output:/app/output \
		-v $(PWD)/archive:/app/archive \
		-v $(PWD)/published:/app/published \
		$(IMAGE_NAME):$(IMAGE_TAG)

# Help target
help:
	@echo "$(GREEN)PocketFlow Document Workflow - Makefile$(NC)"
	@echo ""
	@echo "Available targets:"
	@echo "  $(YELLOW)build$(NC)          - Build the Docker image"
	@echo "  $(YELLOW)run$(NC)            - Run the workflow interactively"
	@echo "  $(YELLOW)test$(NC)           - Run the test suite"
	@echo "  $(YELLOW)shell$(NC)          - Open interactive Python shell"
	@echo "  $(YELLOW)bash$(NC)           - Open bash shell for development"
	@echo "  $(YELLOW)dev$(NC)            - Start development environment with docker-compose"
	@echo "  $(YELLOW)compose-build$(NC)  - Build using docker-compose"
	@echo "  $(YELLOW)compose-run$(NC)    - Run using docker-compose"
	@echo "  $(YELLOW)logs$(NC)           - View container logs"
	@echo "  $(YELLOW)stop$(NC)           - Stop all containers"
	@echo "  $(YELLOW)clean$(NC)          - Clean up Docker resources"
	@echo "  $(YELLOW)clean-output$(NC)   - Remove output directories"
	@echo "  $(YELLOW)clean-all$(NC)      - Full cleanup (Docker + outputs)"
	@echo "  $(YELLOW)check$(NC)          - Check prerequisites"
	@echo "  $(YELLOW)init-dirs$(NC)      - Create output directories"
	@echo "  $(YELLOW)run-custom$(NC)     - Run with custom context (CONTEXT=file.yml)"
	@echo "  $(YELLOW)help$(NC)           - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make build"
	@echo "  make run"
	@echo "  make run-custom CONTEXT=my_context.yml"