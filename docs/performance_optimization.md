# Panduan Optimisasi Kinerja untuk Sistem Balas Email Otomatis

This guide provides detailed strategies and best practices for optimizing the performance of your Auto Reply Email system to ensure it meets the 15-second response time requirement and handles high email volumes efficiently.

## Table of Contents

1. [Performance Requirements](#performance-requirements)
2. [Cloud Function Optimization](#cloud-function-optimization)
3. [API Call Optimization](#api-call-optimization)
4. [Vertex AI Optimization](#vertex-ai-optimization)
5. [Monitoring and Benchmarking](#monitoring-and-benchmarking)
6. [Scaling Strategies](#scaling-strategies)
7. [Advanced Optimization Techniques](#advanced-optimization-techniques)

## Performance Requirements

The Auto Reply Email system has the following key performance requirements:

- **Response Time**: < 15 seconds from email receipt to reply sent
- **Error Rate**: < 1% of emails failing to receive a reply
- **Scalability**: Handle up to 1,000 emails per hour
- **Resource Efficiency**: Minimize compute costs while meeting performance targets

## Cloud Function Optimization

### Memory Allocation

The Cloud Function's memory allocation directly impacts CPU allocation and processing speed:

| Memory | CPU | Relative Performance | Recommended For |
|--------|-----|----------------------|-----------------|
| 128MB  | 0.08 vCPU | Baseline | Low volume (<10/hour) |
| 256MB  | 0.17 vCPU | ~2x faster | Medium volume (10-100/hour) |
| 512MB  | 0.33 vCPU | ~4x faster | High volume (100-500/hour) |
| 1024MB | 0.58 vCPU | ~8x faster | Very high volume (500+/hour) |

**Recommendation**: Start with 256MB and increase if response time exceeds 10 seconds.

```terraform
resource "google_cloudfunctions_function" "function" {
  name        = "auto-reply-email"
  memory      = 256
  # Other configuration...
}
```

### Cold Start Mitigation

Cloud Functions experience "cold starts" when they haven't been invoked recently:

1. **Scheduled Warming**: Set up a Cloud Scheduler job to ping your function every 5-10 minutes:

```terraform
resource "google_cloud_scheduler_job" "warm_function" {
  name        = "warm-email-function"
  schedule    = "*/5 * * * *"  # Every 5 minutes
  
  http_target {
    uri         = google_cloudfunctions_function.function.https_trigger_url
    http_method = "GET"
    headers     = {
      "X-Cloudscheduler" = "true"
    }
  }
}
```

2. **Minimum Instances**: For high-volume scenarios, configure minimum instances:

```terraform
resource "google_cloudfunctions_function" "function" {
  # Other configuration...
  min_instances = 1
}
```

### Function Timeout

Set an appropriate timeout that balances completion needs with resource efficiency:

```terraform
resource "google_cloudfunctions_function" "function" {
  # Other configuration...
  timeout     = 60  # seconds
}
```

**Recommendation**: Set timeout to 60 seconds to allow for retries while preventing resource waste.

## API Call Optimization

### Parallel Processing

Implement parallel API calls where possible:

```python
import asyncio
import aiohttp

async def fetch_data_parallel():
    """Fetch data from multiple APIs in parallel."""
    async with aiohttp.ClientSession() as session:
        # Create tasks for parallel execution
        email_task = asyncio.create_task(get_email_content_async(session, history_id))
        customer_task = asyncio.create_task(verify_customer_async(session, email_address))
        
        # Wait for both tasks to complete
        email_data, customer_info = await asyncio.gather(email_task, customer_task)
        
        return email_data, customer_info
```

### Connection Pooling

Reuse HTTP connections to reduce connection establishment overhead:

```python
# Create a session at module level
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5)
session.mount('https://', HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10))

def api_call(url, data):
    """Make API call using connection pool."""
    return session.post(url, json=data)
```

### Optimized Retry Strategy

Implement an efficient retry strategy with exponential backoff:

```python
def retry_with_backoff(func, max_retries=3, base_delay=0.5, max_delay=8):
    """Retry function with exponential backoff."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        retries = 0
        while True:
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.RequestException, HttpError) as e:
                retries += 1
                if retries > max_retries:
                    raise
                
                # Calculate delay with jitter
                delay = min(base_delay * (2 ** (retries - 1)), max_delay)
                jitter = random.uniform(0, 0.1 * delay)
                sleep_time = delay + jitter
                
                logging.warning(f"Retry {retries}/{max_retries} after {sleep_time:.2f}s due to: {str(e)}")
                time.sleep(sleep_time)
    
    return wrapper
```

## Vertex AI Optimization

### Model Selection

Choose the appropriate Vertex AI model based on your requirements:

| Model | Response Quality | Speed | Cost | Use Case |
|-------|------------------|-------|------|----------|
| gemini-1.0-pro | Highest | Slower | Higher | Complex emails requiring nuance |
| gemini-1.0-pro-vision | High | Slower | Higher | Emails with images/attachments |
| text-bison | Good | Faster | Lower | Simple, text-only emails |

**Recommendation**: Use `text-bison` for simple inquiries and `gemini-1.0-pro` for complex emails.

### Prompt Optimization

1. **Reduce Token Count**: Keep prompts concise while maintaining context:

```python
def create_optimized_prompt(sender, subject, body, tone, customer_info=None):
    """Create optimized prompt with reduced tokens."""
    # Extract only relevant parts of the email body
    body_summary = summarize_email(body, max_length=200)
    
    prompt = f"""
    You are a professional email assistant. Write a {tone} reply to this email:
    From: {sender}
    Subject: {subject}
    Content: {body_summary}
    """
    
    if customer_info:
        # Include only essential customer information
        prompt += f"\nCustomer: {customer_info.get('name', 'Unknown')}, Status: {customer_info.get('status', 'Regular')}"
    
    prompt += "\nKeep your reply concise and directly address the inquiry."
    
    return prompt
```

2. **Caching Common Responses**: Implement a response cache for frequently asked questions:

```python
from google.cloud import storage
import hashlib
import json

def get_cached_response(sender, subject, body):
    """Get cached response if available."""
    # Create a hash of the email content
    content_hash = hashlib.md5(f"{subject}:{body}".encode()).hexdigest()
    
    # Check if response exists in cache
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket("email-response-cache")
        blob = bucket.blob(f"responses/{content_hash}.json")
        
        if blob.exists():
            cached_data = json.loads(blob.download_as_string())
            if time.time() - cached_data["timestamp"] < 86400:  # 24 hours
                return cached_data["response"]
    except Exception:
        pass
    
    return None

def save_to_cache(sender, subject, body, response):
    """Save response to cache."""
    content_hash = hashlib.md5(f"{subject}:{body}".encode()).hexdigest()
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket("email-response-cache")
        blob = bucket.blob(f"responses/{content_hash}.json")
        
        cached_data = {
            "timestamp": time.time(),
            "response": response
        }
        blob.upload_from_string(json.dumps(cached_data))
    except Exception:
        pass
```

### Parameter Tuning

Optimize Vertex AI parameters for faster responses:

```python
def generate_optimized_ai_reply(prompt):
    """Generate AI reply with optimized parameters."""
    model = GenerativeModel("gemini-1.0-pro")
    
    # Optimize for speed with these parameters
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,       # Lower temperature for more deterministic responses
            "max_output_tokens": 800, # Limit response length
            "top_p": 0.95,            # Slightly higher top_p for faster sampling
            "top_k": 40               # Standard top_k
        }
    )
    
    return response.text
```

## Monitoring and Benchmarking

### Performance Metrics

Track these key metrics to identify optimization opportunities:

1. **End-to-End Latency Breakdown**:

```python
def process_email(email_address, history_id):
    """Process email with performance tracking."""
    metrics = {
        "start_time": time.time(),
        "steps": {}
    }
    
    try:
        # Initialize Gmail API service
        step_start = time.time()
        credentials = get_secret("gmail-oauth-token")
        service = initialize_gmail_service(credentials)
        metrics["steps"]["gmail_init"] = time.time() - step_start
        
        # Get email content
        step_start = time.time()
        email_data = get_email_content(service, history_id)
        metrics["steps"]["email_retrieval"] = time.time() - step_start
        
        # Verify customer
        step_start = time.time()
        customer_info = verify_customer(email_data.get("from", ""))
        metrics["steps"]["customer_verification"] = time.time() - step_start
        
        # Generate AI reply
        step_start = time.time()
        reply_text = generate_ai_reply(
            email_data.get("from", ""), 
            email_data.get("subject", ""), 
            email_data.get("body", ""),
            "formal", 
            customer_info
        )
        metrics["steps"]["ai_generation"] = time.time() - step_start
        
        # Send reply
        step_start = time.time()
        success = send_reply(
            service, 
            email_data.get("from", ""), 
            email_data.get("subject", ""), 
            reply_text
        )
        metrics["steps"]["send_reply"] = time.time() - step_start
        
        metrics["total_time"] = time.time() - metrics["start_time"]
        metrics["success"] = success
        
        # Log performance metrics
        logging.info(json.dumps(metrics))
        
        return success
        
    except Exception as e:
        metrics["error"] = str(e)
        metrics["total_time"] = time.time() - metrics["start_time"]
        logging.error(json.dumps(metrics))
        return False
```

2. **Custom Metrics in Cloud Monitoring**:

```python
from google.cloud import monitoring_v3

def record_custom_metrics(metrics):
    """Record custom metrics to Cloud Monitoring."""
    client = monitoring_v3.MetricServiceClient()
    project_name = client.project_path(os.environ.get("GCP_PROJECT_ID"))
    
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/auto_reply/response_time"
    
    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10**9)
    
    point = series.points.add()
    point.value.double_value = metrics["total_time"]
    point.interval.end_time.seconds = seconds
    point.interval.end_time.nanos = nanos
    
    client.create_time_series(name=project_name, time_series=[series])
```

### Benchmarking Tool

Create a benchmarking script to test system performance:

```python
def benchmark_system(num_requests=100, concurrency=10):
    """Benchmark system performance."""
    results = {
        "total_requests": num_requests,
        "successful": 0,
        "failed": 0,
        "response_times": [],
        "errors": []
    }
    
    # Generate test data
    test_emails = [
        {
            "subject": f"Test Email {i}",
            "body": f"This is test email {i} for benchmarking.",
            "from": f"test{i}@example.com"
        }
        for i in range(num_requests)
    ]
    
    async def process_batch(batch):
        tasks = []
        for email in batch:
            task = asyncio.create_task(
                process_email_async(email["from"], "12345", email)
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process in batches
    batches = [test_emails[i:i+concurrency] for i in range(0, len(test_emails), concurrency)]
    
    for batch in batches:
        batch_results = asyncio.run(process_batch(batch))
        
        for result in batch_results:
            if isinstance(result, Exception):
                results["failed"] += 1
                results["errors"].append(str(result))
            else:
                results["successful"] += 1
                results["response_times"].append(result["total_time"])
    
    # Calculate statistics
    if results["response_times"]:
        results["avg_response_time"] = sum(results["response_times"]) / len(results["response_times"])
        results["min_response_time"] = min(results["response_times"])
        results["max_response_time"] = max(results["response_times"])
        results["p95_response_time"] = sorted(results["response_times"])[int(len(results["response_times"]) * 0.95)]
    
    return results
```

## Scaling Strategies

### Pub/Sub Configuration

Optimize Pub/Sub for high throughput:

```terraform
resource "google_pubsub_subscription" "email_subscription" {
  name  = "email-subscriber"
  topic = google_pubsub_topic.email_topic.name
  
  # Increase message retention
  message_retention_duration = "86400s"  # 24 hours
  
  # Configure acknowledgement deadline
  ack_deadline_seconds = 60
  
  # Configure retry policy
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"  # 10 minutes
  }
  
  # Enable message ordering if needed
  enable_message_ordering = false
}
```

### Multi-Region Deployment

Deploy to multiple regions for improved availability and latency:

```terraform
# Define regions
locals {
  regions = ["us-central1", "us-east1", "europe-west1"]
}

# Deploy function to multiple regions
resource "google_cloudfunctions_function" "multi_region_function" {
  for_each    = toset(local.regions)
  name        = "auto-reply-email-${each.value}"
  region      = each.value
  # Other configuration...
}

# Set up load balancing
resource "google_compute_global_address" "default" {
  name = "auto-reply-email-lb-ip"
}

resource "google_compute_backend_service" "default" {
  name      = "auto-reply-email-backend"
  protocol  = "HTTP"
  timeout_sec = 30
  
  dynamic "backend" {
    for_each = local.regions
    content {
      group = google_compute_region_network_endpoint_group.function_neg[backend.value].self_link
    }
  }
}
```

## Advanced Optimization Techniques

### Content-Based Routing

Route emails to different processing paths based on complexity:

```python
def determine_email_complexity(subject, body):
    """Determine email complexity to route appropriately."""
    # Simple heuristics for complexity
    complexity = 0
    
    # Check email length
    if len(body) > 500:
        complexity += 2
    elif len(body) > 200:
        complexity += 1
    
    # Check for questions
    question_count = body.count("?")
    complexity += min(question_count, 3)
    
    # Check for complex topics
    complex_topics = ["technical", "bug", "error", "problem", "issue", "broken"]
    for topic in complex_topics:
        if topic in body.lower() or topic in subject.lower():
            complexity += 1
    
    # Categorize
    if complexity >= 5:
        return "high"
    elif complexity >= 2:
        return "medium"
    else:
        return "low"

def process_email_by_complexity(email_data):
    """Process email based on complexity."""
    complexity = determine_email_complexity(
        email_data.get("subject", ""), 
        email_data.get("body", "")
    )
    
    if complexity == "low":
        # Use faster model with simpler prompt
        model = "text-bison"
        max_tokens = 400
    elif complexity == "medium":
        # Use balanced approach
        model = "gemini-1.0-pro"
        max_tokens = 600
    else:
        # Use most capable model with comprehensive prompt
        model = "gemini-1.0-pro"
        max_tokens = 1024
    
    return generate_ai_reply_with_model(
        email_data.get("from", ""),
        email_data.get("subject", ""),
        email_data.get("body", ""),
        "formal",
        customer_info=None,
        model=model,
        max_tokens=max_tokens
    )
```

### Precomputed Responses

Implement precomputed responses for common queries:

```python
# Define common patterns and responses
COMMON_PATTERNS = {
    r"(?i).*hours.*open.*": {
        "response": "Thank you for your inquiry about our hours. We are open Monday through Friday from 9 AM to 6 PM, and Saturday from 10 AM to 4 PM. We are closed on Sundays and major holidays.",
        "confidence_threshold": 0.8
    },
    r"(?i).*return.*policy.*": {
        "response": "Thank you for asking about our return policy. We offer a 30-day satisfaction guarantee on all purchases. If you're not completely satisfied, you can return your item for a full refund within 30 days of purchase.",
        "confidence_threshold": 0.8
    }
}

def check_for_common_patterns(subject, body):
    """Check if email matches common patterns for precomputed responses."""
    combined_text = f"{subject} {body}"
    
    for pattern, config in COMMON_PATTERNS.items():
        match = re.search(pattern, combined_text)
        if match:
            # Calculate confidence based on match length vs. text length
            match_length = match.end() - match.start()
            confidence = min(1.0, match_length / len(combined_text) * 2)
            
            if confidence >= config["confidence_threshold"]:
                return config["response"]
    
    return None
```

### Response Caching with Redis

Implement a Redis cache for faster response retrieval:

```python
import redis
import hashlib
import json

# Initialize Redis client
redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    db=0
)

def get_cached_response_redis(sender, subject, body):
    """Get cached response from Redis if available."""
    # Create a hash of the email content
    content_hash = hashlib.md5(f"{subject}:{body}".encode()).hexdigest()
    
    # Check if response exists in cache
    cached_data = redis_client.get(f"email:response:{content_hash}")
    if cached_data:
        return json.loads(cached_data)
    
    return None

def save_to_cache_redis(sender, subject, body, response):
    """Save response to Redis cache."""
    content_hash = hashlib.md5(f"{subject}:{body}".encode()).hexdigest()
    
    cached_data = {
        "timestamp": time.time(),
        "response": response
    }
    
    # Cache for 24 hours
    redis_client.setex(
        f"email:response:{content_hash}",
        86400,  # 24 hours
        json.dumps(cached_data)
    )
```

## Conclusion

By implementing these optimization strategies, you can significantly improve the performance of your Auto Reply Email system. Start with the basic optimizations and progressively implement more advanced techniques as needed based on your monitoring data.

Remember that optimization is an iterative process:

1. **Measure** current performance using detailed metrics
2. **Identify** bottlenecks and performance issues
3. **Implement** targeted optimizations
4. **Validate** improvements through benchmarking
5. **Repeat** the process to continuously improve

With careful optimization, your system can consistently achieve sub-15-second response times while maintaining high quality replies and efficiently handling large email volumes.
