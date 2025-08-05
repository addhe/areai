# Auto Reply Email with AI (Vertex AI Gemini)
# Makefile for development and deployment tasks

.PHONY: setup install test lint deploy-function deploy-infra clean auth watch

# Variables
PROJECT_ID ?= $(shell gcloud config get-value project)
REGION ?= us-central1
ENV ?= dev
FUNCTION_NAME = auto-reply-email
TOPIC_NAME = new-email
SERVICE_ACCOUNT = autoreply-sa@$(PROJECT_ID).iam.gserviceaccount.com

# Setup development environment
setup:
	@echo "Setting up development environment..."
	python -m venv .venv
	@echo "Virtual environment created. Activate with: source .venv/bin/activate"

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r cloud_function/requirements.txt
	pip install pytest pytest-cov flake8 black isort

# Run tests
test:
	@echo "Running tests..."
	pytest tests/unit/ -v
	pytest tests/integration/ -v

# Run tests with coverage
test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=cloud_function tests/ --cov-report=term --cov-report=html
	@echo "Coverage report generated in htmlcov/"

# Lint code
lint:
	@echo "Linting code..."
	flake8 cloud_function/ scripts/ tests/
	black --check cloud_function/ scripts/ tests/
	isort --check cloud_function/ scripts/ tests/

# Format code
format:
	@echo "Formatting code..."
	black cloud_function/ scripts/ tests/
	isort cloud_function/ scripts/ tests/

# Deploy Cloud Function
deploy-function:
	@echo "Deploying Cloud Function to $(ENV) environment..."
	gcloud functions deploy $(FUNCTION_NAME) \
		--runtime python311 \
		--trigger-topic $(TOPIC_NAME) \
		--entry-point pubsub_trigger \
		--service-account $(SERVICE_ACCOUNT) \
		--region $(REGION) \
		--memory 256MB \
		--timeout 60s \
		--source cloud_function/ \
		--set-env-vars GCP_PROJECT_ID=$(PROJECT_ID),GCP_REGION=$(REGION)

# Deploy infrastructure with Terraform
deploy-infra:
	@echo "Deploying infrastructure with Terraform..."
	cd terraform && \
	terraform init && \
	terraform validate && \
	terraform plan -var="project_id=$(PROJECT_ID)" -var="region=$(REGION)" -out=tfplan && \
	terraform apply tfplan

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf .venv/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	find . -type d -name __pycache__ -exec rm -rf {} +

# Setup Gmail API authentication
auth:
	@echo "Setting up Gmail API authentication..."
	python scripts/gmail_auth.py

# Setup Gmail API watch
watch:
	@echo "Setting up Gmail API watch..."
	python scripts/gmail_auth.py --setup-watch

# Test email flow
test-email:
	@echo "Testing email flow..."
	python scripts/test_email.py --to $(TO)

# View Cloud Function logs
logs:
	@echo "Viewing Cloud Function logs..."
	gcloud functions logs read $(FUNCTION_NAME) --limit 50

# Help
help:
	@echo "Auto Reply Email with AI (Vertex AI Gemini)"
	@echo ""
	@echo "Available commands:"
	@echo "  setup           - Set up development environment"
	@echo "  install         - Install dependencies"
	@echo "  test            - Run tests"
	@echo "  test-coverage   - Run tests with coverage"
	@echo "  lint            - Lint code"
	@echo "  format          - Format code"
	@echo "  deploy-function - Deploy Cloud Function"
	@echo "  deploy-infra    - Deploy infrastructure with Terraform"
	@echo "  clean           - Clean up"
	@echo "  auth            - Setup Gmail API authentication"
	@echo "  watch           - Setup Gmail API watch"
	@echo "  test-email      - Test email flow (TO=email@example.com)"
	@echo "  logs            - View Cloud Function logs"
	@echo ""
	@echo "Environment variables:"
	@echo "  PROJECT_ID      - GCP project ID (default: current gcloud project)"
	@echo "  REGION          - GCP region (default: us-central1)"
	@echo "  ENV             - Environment (default: dev)"
	@echo "  TO              - Recipient email for test-email command"

# Default target
.DEFAULT_GOAL := help
