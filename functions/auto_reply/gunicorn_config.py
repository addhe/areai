"""
Gunicorn configuration file for Cloud Run
"""
import os
import multiprocessing

# Increase timeouts to prevent worker timeouts
timeout = 300  # Increase from default 30 seconds to 300 seconds to match Cloud Run timeout
graceful_timeout = 120

# Worker settings - use single worker with threads for Cloud Run
workers = 1
threads = 8
worker_class = 'gthread'  # Use gthread instead of sync for better thread handling

# Logging - more verbose for debugging
loglevel = 'debug'
accesslog = '-'  # stdout
errorlog = '-'  # stderr
capture_output = True
enable_stdio_inheritance = True

# Bind to port from environment variable
port = os.environ.get('PORT', '8080')
bind = f"0.0.0.0:{port}"

# Prevent Gunicorn from restarting workers too aggressively
max_requests = 1200
max_requests_jitter = 50

# Preload app to avoid import errors
preload_app = True
