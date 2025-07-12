#!/bin/bash
# Docker entrypoint script for PocketFlow Document Workflow

set -e

# Function to display help
show_help() {
    echo "PocketFlow Document Workflow Container"
    echo "====================================="
    echo ""
    echo "Usage:"
    echo "  docker run -it pocketflow-document-workflow [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  workflow          Run the main document workflow (default)"
    echo "  test              Run the test suite"
    echo "  shell             Start an interactive Python shell"
    echo "  bash              Start a bash shell"
    echo "  custom <file>     Run a custom Python workflow file"
    echo "  help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  docker run -it pocketflow-document-workflow"
    echo "  docker run -it pocketflow-document-workflow test"
    echo "  docker run -it -v ./my_context.yml:/app/context.yml pocketflow-document-workflow"
    echo "  docker run -it -v ./my_workflow.py:/app/my_workflow.py pocketflow-document-workflow custom my_workflow.py"
}

# Main entrypoint logic
case "${1:-workflow}" in
    workflow)
        echo "Starting Document Workflow..."
        echo "============================"
        exec python3 document_workflow.py
        ;;
    
    test)
        echo "Running Tests..."
        echo "================"
        exec python3 test_document_workflow.py
        ;;
    
    shell)
        echo "Starting Python Interactive Shell..."
        echo "==================================="
        exec python3 -i -c "
from document_workflow import *
print('PocketFlow Document Workflow loaded.')
print('Available classes: DocumentWorkflow, WorkingGroupFlow, CommitteeFlow')
print('Example: workflow = DocumentWorkflow()')
"
        ;;
    
    bash)
        exec /bin/bash
        ;;
    
    custom)
        if [ -z "$2" ]; then
            echo "Error: Please specify a Python file to run"
            exit 1
        fi
        echo "Running custom workflow: $2"
        echo "=========================="
        shift
        exec python3 "$@"
        ;;
    
    help|--help|-h)
        show_help
        exit 0
        ;;
    
    *)
        # If the first argument doesn't match any command, pass all arguments to python3
        exec python3 "$@"
        ;;
esac