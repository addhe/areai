FROM python:3.11-slim

WORKDIR /app

# Copy requirements dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# API configuration - these should be provided during build or runtime
ARG CUSTOMER_API_ENDPOINT
ENV CUSTOMER_API_ENDPOINT=${CUSTOMER_API_ENDPOINT:-"https://nasabah-api-endpoint.example.com"}

# Email configuration
ARG DESTINATION_EMAIL
ENV DESTINATION_EMAIL=${DESTINATION_EMAIL:-"addhe.warman+cs@gmail.com"}

# Expose port untuk Cloud Run
EXPOSE 8080

# Run the application with gunicorn for production
CMD exec gunicorn --bind :8080 --workers 1 --threads 8 --timeout 0 cloud_run_server:app
