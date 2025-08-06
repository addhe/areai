# Panduan Penskalaan untuk Sistem Balas Email Otomatis

This guide provides strategies and best practices for scaling the Auto Reply Email system to handle enterprise workloads and high email volumes.

## Table of Contents

1. [Scaling Requirements](#scaling-requirements)
2. [Infrastructure Scaling](#infrastructure-scaling)
3. [Performance Optimization](#performance-optimization)
4. [Multi-User Support](#multi-user-support)
5. [High Availability](#high-availability)
6. [Cost Optimization](#cost-optimization)
7. [Implementation Roadmap](#implementation-roadmap)

## Scaling Requirements

Before implementing scaling strategies, assess your requirements:

| Scale Level | Email Volume | Response Time | Concurrent Users | Infrastructure |
|-------------|--------------|---------------|------------------|---------------|
| Small | < 100/day | < 15 seconds | 1-5 | Single region, basic |
| Medium | 100-1,000/day | < 10 seconds | 5-20 | Single region, optimized |
| Large | 1,000-10,000/day | < 5 seconds | 20-100 | Multi-region, advanced |
| Enterprise | > 10,000/day | < 3 seconds | > 100 | Global, fully managed |

## Infrastructure Scaling

### Cloud Function Scaling

1. **Memory and CPU Allocation**

Increase memory allocation to improve performance:

```terraform
resource "google_cloudfunctions_function" "function" {
  name        = "auto-reply-email"
  memory      = 1024  # 1GB for high volume
  # Other configuration...
}
```

2. **Minimum Instances**

Configure minimum instances to eliminate cold starts:

```terraform
resource "google_cloudfunctions_function" "function" {
  # Other configuration...
  min_instances = 5
  max_instances = 100
}
```

3. **Regional Deployment**

Deploy to multiple regions for improved latency and availability:

```terraform
locals {
  regions = ["us-central1", "us-east1", "europe-west1", "asia-east1"]
}

resource "google_cloudfunctions_function" "multi_region_function" {
  for_each    = toset(local.regions)
  name        = "auto-reply-email-${each.value}"
  region      = each.value
  # Other configuration...
}
```

### Pub/Sub Scaling

1. **Topic Configuration**

Optimize Pub/Sub for high throughput:

```terraform
resource "google_pubsub_topic" "email_topic" {
  name = "email-notifications"
  
  # Enable message storage policy
  message_storage_policy {
    allowed_persistence_regions = [
      "us-central1",
      "us-east1"
    ]
  }
}
```

2. **Subscription Configuration**

Configure subscription for reliable delivery:

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
  
  # Enable exactly-once delivery
  enable_exactly_once_delivery = true
}
```

### Load Balancing

Implement load balancing for multi-region deployments:

```terraform
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
  
  # Enable Cloud CDN for static content
  enable_cdn = true
}
```

## Performance Optimization

### Parallel Processing

Implement parallel processing for improved throughput:

```python
import asyncio
import aiohttp

async def process_emails_batch(batch):
    """Process a batch of emails in parallel."""
    tasks = []
    async with aiohttp.ClientSession() as session:
        for email in batch:
            task = asyncio.create_task(process_single_email(session, email))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successes = sum(1 for r in results if r is True)
    failures = sum(1 for r in results if r is False or isinstance(r, Exception))
    
    logging.info(f"Batch processing complete: {successes} successes, {failures} failures")
    return successes, failures

async def process_single_email(session, email):
    """Process a single email with async operations."""
    try:
        # Get email content and customer info in parallel
        email_task = asyncio.create_task(get_email_content_async(session, email['history_id']))
        customer_task = asyncio.create_task(verify_customer_async(session, email['email_address']))
        
        email_data, customer_info = await asyncio.gather(email_task, customer_task)
        
        # Generate AI reply (this is still synchronous)
        reply = generate_ai_reply(
            email_data.get("from", ""),
            email_data.get("subject", ""),
            email_data.get("body", ""),
            "formal",
            customer_info
        )
        
        # Send reply
        success = await send_reply_async(session, email_data.get("from", ""), 
                                        email_data.get("subject", ""), reply)
        
        return success
    except Exception as e:
        logging.error(f"Error processing email: {str(e)}")
        return False
```

### Caching Strategy

Implement multi-level caching:

```python
from google.cloud import redis_v1
from google.cloud import storage
import hashlib
import json

# Initialize Redis client
redis_client = redis_v1.CloudRedisClient()
redis_instance_name = redis_client.instance_path(
    os.environ.get("GCP_PROJECT_ID"),
    os.environ.get("GCP_REGION"),
    "auto-reply-cache"
)

def get_cached_response(sender, subject, body):
    """Get cached response using multi-level caching."""
    # Create a hash of the email content
    content_hash = hashlib.md5(f"{subject}:{body}".encode()).hexdigest()
    
    # Check in-memory cache first (fastest)
    if hasattr(get_cached_response, "cache") and content_hash in get_cached_response.cache:
        return get_cached_response.cache[content_hash]
    
    # Check Redis cache next (fast)
    try:
        import redis
        r = redis.Redis(host=os.environ.get("REDIS_HOST"), port=6379, db=0)
        cached_data = r.get(f"email:response:{content_hash}")
        if cached_data:
            response = json.loads(cached_data)
            # Update in-memory cache
            if not hasattr(get_cached_response, "cache"):
                get_cached_response.cache = {}
            get_cached_response.cache[content_hash] = response
            return response
    except Exception:
        pass
    
    # Check Cloud Storage cache last (slower)
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(f"{os.environ.get('GCP_PROJECT_ID')}-response-cache")
        blob = bucket.blob(f"responses/{content_hash}.json")
        
        if blob.exists():
            cached_data = json.loads(blob.download_as_string())
            if time.time() - cached_data["timestamp"] < 86400:  # 24 hours
                # Update Redis and in-memory cache
                try:
                    r.setex(
                        f"email:response:{content_hash}",
                        3600,  # 1 hour
                        json.dumps(cached_data)
                    )
                except Exception:
                    pass
                
                if not hasattr(get_cached_response, "cache"):
                    get_cached_response.cache = {}
                get_cached_response.cache[content_hash] = cached_data["response"]
                
                return cached_data["response"]
    except Exception:
        pass
    
    return None
```

### Database Sharding

For high-volume deployments, implement database sharding:

```python
def get_shard_id(email_address):
    """Determine shard ID based on email address."""
    import hashlib
    hash_value = int(hashlib.md5(email_address.encode()).hexdigest(), 16)
    return hash_value % 10  # 10 shards

def get_firestore_collection(email_address):
    """Get the appropriate Firestore collection based on sharding."""
    shard_id = get_shard_id(email_address)
    return f"processed_emails_shard_{shard_id}"

def mark_email_processed(email_address, message_id):
    """Mark email as processed in the appropriate shard."""
    from google.cloud import firestore
    db = firestore.Client()
    
    collection_name = get_firestore_collection(email_address)
    doc_ref = db.collection(collection_name).document(message_id)
    
    doc_ref.set({
        'email_address': email_address,
        'processed_at': firestore.SERVER_TIMESTAMP,
        'shard_id': get_shard_id(email_address)
    })
```

## Multi-User Support

### Multi-Tenant Architecture

1. **Tenant Isolation**

Implement tenant isolation for multi-user support:

```python
def get_tenant_config(email_address):
    """Get tenant configuration based on email domain."""
    from google.cloud import firestore
    db = firestore.Client()
    
    # Extract domain from email
    domain = email_address.split('@')[-1]
    
    # Get tenant configuration
    tenant_ref = db.collection('tenants').document(domain)
    tenant = tenant_ref.get()
    
    if tenant.exists:
        return tenant.to_dict()
    else:
        # Return default configuration
        return {
            'tenant_id': 'default',
            'ai_model': 'gemini-1.0-pro',
            'response_tone': 'formal',
            'max_tokens': 800
        }
```

2. **Per-Tenant OAuth**

Manage OAuth tokens per tenant:

```python
def get_tenant_oauth_token(tenant_id):
    """Get OAuth token for specific tenant."""
    from google.cloud import secretmanager
    
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{os.environ.get('GCP_PROJECT_ID')}/secrets/gmail-oauth-{tenant_id}/versions/latest"
    
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logging.error(f"Error retrieving token for tenant {tenant_id}: {str(e)}")
        raise
```

3. **Tenant-Specific Processing**

Implement tenant-specific email processing:

```python
def process_email_for_tenant(tenant_id, email_data):
    """Process email according to tenant configuration."""
    # Get tenant configuration
    tenant_config = get_tenant_config_by_id(tenant_id)
    
    # Initialize services with tenant credentials
    credentials = get_tenant_oauth_token(tenant_id)
    service = initialize_gmail_service(credentials)
    
    # Process with tenant-specific settings
    customer_info = verify_customer(email_data.get("from", ""), tenant_id)
    
    reply = generate_ai_reply(
        email_data.get("from", ""),
        email_data.get("subject", ""),
        email_data.get("body", ""),
        tenant_config.get("response_tone", "formal"),
        customer_info,
        model=tenant_config.get("ai_model", "gemini-1.0-pro"),
        max_tokens=tenant_config.get("max_tokens", 800)
    )
    
    success = send_reply(
        service,
        email_data.get("from", ""),
        email_data.get("subject", ""),
        reply,
        tenant_config.get("email_template")
    )
    
    return success
```

### User Management

Implement a user management system:

```python
def create_tenant(domain, admin_email, display_name):
    """Create a new tenant in the system."""
    from google.cloud import firestore
    db = firestore.Client()
    
    # Create tenant document
    tenant_ref = db.collection('tenants').document(domain)
    tenant_ref.set({
        'domain': domain,
        'admin_email': admin_email,
        'display_name': display_name,
        'created_at': firestore.SERVER_TIMESTAMP,
        'status': 'active',
        'ai_model': 'gemini-1.0-pro',
        'response_tone': 'formal',
        'max_tokens': 800
    })
    
    # Create admin user
    admin_ref = db.collection('users').document(admin_email)
    admin_ref.set({
        'email': admin_email,
        'tenant_id': domain,
        'role': 'admin',
        'created_at': firestore.SERVER_TIMESTAMP,
        'status': 'active'
    })
    
    return tenant_ref.id


def add_tenant_user(tenant_id, email, role='user'):
    """Add a user to a tenant."""
    from google.cloud import firestore
    db = firestore.Client()
    
    # Verify tenant exists
    tenant_ref = db.collection('tenants').document(tenant_id)
    tenant = tenant_ref.get()
    
    if not tenant.exists:
        raise ValueError(f"Tenant {tenant_id} does not exist")
    
    # Create user
    user_ref = db.collection('users').document(email)
    user_ref.set({
        'email': email,
        'tenant_id': tenant_id,
        'role': role,
        'created_at': firestore.SERVER_TIMESTAMP,
        'status': 'active'
    })
    
    return user_ref.id
```

## High Availability

### Regional Redundancy

1. **Multi-Region Deployment**

Deploy the system across multiple regions for high availability:

```terraform
locals {
  primary_region = "us-central1"
  dr_regions     = ["us-east1", "europe-west1", "asia-east1"]
  all_regions    = concat([local.primary_region], local.dr_regions)
}

# Deploy Cloud Functions to all regions
resource "google_cloudfunctions_function" "auto_reply_function" {
  for_each    = toset(local.all_regions)
  name        = "auto-reply-email-${each.value}"
  region      = each.value
  runtime     = "python310"
  # Other configuration...
}

# Deploy Pub/Sub topics with regional routing
resource "google_pubsub_topic" "email_topic" {
  for_each = toset(local.all_regions)
  name     = "email-notifications-${each.value}"
  
  message_storage_policy {
    allowed_persistence_regions = [each.value]
  }
}
```

2. **Regional Failover**

Implement automatic failover between regions:

```python
def get_active_region():
    """Get the currently active region for processing."""
    from google.cloud import storage
    
    client = storage.Client()
    bucket = client.bucket(f"{os.environ.get('GCP_PROJECT_ID')}-config")
    blob = bucket.blob("active_region.txt")
    
    try:
        return blob.download_as_string().decode('utf-8').strip()
    except Exception:
        # Default to primary region
        return "us-central1"

def switch_active_region(new_region):
    """Switch the active region for processing."""
    from google.cloud import storage
    
    client = storage.Client()
    bucket = client.bucket(f"{os.environ.get('GCP_PROJECT_ID')}-config")
    blob = bucket.blob("active_region.txt")
    
    blob.upload_from_string(new_region)
    logging.info(f"Switched active region to {new_region}")
```

### Health Checks

1. **Automated Health Checks**

Implement health checks to monitor system components:

```python
def check_system_health():
    """Check the health of all system components."""
    health_status = {
        'gmail_api': check_gmail_api_health(),
        'pubsub': check_pubsub_health(),
        'vertex_ai': check_vertex_ai_health(),
        'cloud_functions': check_cloud_functions_health(),
        'secret_manager': check_secret_manager_health()
    }
    
    # Calculate overall health
    overall_health = all(status for status in health_status.values())
    
    # Log health status
    logging.info(f"System health check: {'HEALTHY' if overall_health else 'UNHEALTHY'}")
    for component, status in health_status.items():
        logging.info(f"  {component}: {'HEALTHY' if status else 'UNHEALTHY'}")
    
    return overall_health, health_status

def check_gmail_api_health():
    """Check Gmail API health."""
    try:
        # Load credentials
        credentials = load_credentials_from_secret_manager(os.environ.get('GCP_PROJECT_ID'))
        service = build('gmail', 'v1', credentials=credentials)
        
        # Make a simple API call
        service.users().getProfile(userId='me').execute()
        return True
    except Exception as e:
        logging.error(f"Gmail API health check failed: {str(e)}")
        return False
```

2. **Circuit Breakers**

Implement circuit breakers to prevent cascading failures:

```python
class CircuitBreaker:
    """Circuit breaker implementation for external service calls."""
    
    def __init__(self, name, failure_threshold=5, reset_timeout=60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.last_failure_time = 0
    
    def execute(self, func, *args, **kwargs):
        """Execute function with circuit breaker pattern."""
        # Check if circuit is OPEN
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                # Try to move to HALF-OPEN state
                self.state = "HALF-OPEN"
                logging.info(f"Circuit {self.name} moved from OPEN to HALF-OPEN")
            else:
                # Circuit is still OPEN, fail fast
                logging.warning(f"Circuit {self.name} is OPEN, failing fast")
                raise Exception(f"Circuit {self.name} is OPEN")
        
        try:
            # Execute function
            result = func(*args, **kwargs)
            
            # If successful in HALF-OPEN, move to CLOSED
            if self.state == "HALF-OPEN":
                self.state = "CLOSED"
                self.failures = 0
                logging.info(f"Circuit {self.name} moved from HALF-OPEN to CLOSED")
            
            return result
        except Exception as e:
            # Record failure
            self.failures += 1
            self.last_failure_time = time.time()
            
            # Check if threshold reached
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logging.error(f"Circuit {self.name} moved to OPEN after {self.failures} failures")
            
            raise e

# Example usage
vertex_ai_circuit = CircuitBreaker("vertex_ai", failure_threshold=3, reset_timeout=300)

def generate_ai_reply_with_circuit_breaker(*args, **kwargs):
    """Generate AI reply with circuit breaker."""
    return vertex_ai_circuit.execute(generate_ai_reply, *args, **kwargs)
```

## Cost Optimization

### Resource Optimization

1. **Tiered Processing**

Implement tiered processing based on email priority:

```python
def determine_email_priority(email_data):
    """Determine email priority for processing."""
    # Check if sender is in VIP list
    sender = email_data.get("from", "")
    if is_vip_sender(sender):
        return "high"
    
    # Check if subject contains urgent keywords
    subject = email_data.get("subject", "").lower()
    urgent_keywords = ["urgent", "important", "asap", "emergency"]
    if any(keyword in subject for keyword in urgent_keywords):
        return "high"
    
    # Check if this is a reply to an existing thread
    if "re:" in subject.lower():
        return "medium"
    
    # Default priority
    return "normal"

def process_email_by_priority(email_data):
    """Process email based on priority."""
    priority = determine_email_priority(email_data)
    
    if priority == "high":
        # Use premium model with higher token limit
        model = "gemini-1.0-ultra"
        max_tokens = 1000
    elif priority == "medium":
        # Use standard model
        model = "gemini-1.0-pro"
        max_tokens = 800
    else:  # normal
        # Use efficient model
        model = "gemini-1.0-pro"
        max_tokens = 500
    
    # Generate reply with appropriate model
    reply = generate_ai_reply(
        email_data.get("from", ""),
        email_data.get("subject", ""),
        email_data.get("body", ""),
        "formal",
        get_customer_info(email_data.get("from", "")),
        model=model,
        max_tokens=max_tokens
    )
    
    return reply
```

2. **Scheduled Scaling**

Implement scheduled scaling based on usage patterns:

```terraform
resource "google_cloud_scheduler_job" "scale_up_job" {
  name      = "scale-up-auto-reply"
  schedule  = "0 8 * * 1-5"  # 8 AM Monday-Friday
  time_zone = "America/New_York"
  
  http_target {
    uri         = "https://us-central1-${var.project_id}.cloudfunctions.net/scale-auto-reply"
    http_method = "POST"
    body        = base64encode(jsonencode({
      "action": "scale_up",
      "min_instances": 10
    }))
  }
}

resource "google_cloud_scheduler_job" "scale_down_job" {
  name      = "scale-down-auto-reply"
  schedule  = "0 18 * * 1-5"  # 6 PM Monday-Friday
  time_zone = "America/New_York"
  
  http_target {
    uri         = "https://us-central1-${var.project_id}.cloudfunctions.net/scale-auto-reply"
    http_method = "POST"
    body        = base64encode(jsonencode({
      "action": "scale_down",
      "min_instances": 2
    }))
  }
}
```

3. **Cost Monitoring**

Implement cost monitoring and alerting:

```python
def monitor_daily_costs():
    """Monitor daily costs and send alerts if thresholds are exceeded."""
    from google.cloud import monitoring_v3
    
    client = monitoring_v3.QueryServiceClient()
    project_name = f"projects/{os.environ.get('GCP_PROJECT_ID')}"
    
    # Query for daily cost
    query = '''
    fetch billing.googleapis.com/billing_account/cost
    | filter resource.project_id = "{}"  
    | align day
    | every 1d
    | group_by [], sum(value.cost)
    '''.format(os.environ.get('GCP_PROJECT_ID'))
    
    results = client.query_time_series(
        request={"name": project_name, "query": query}
    )
    
    # Check if daily cost exceeds threshold
    for result in results.time_series:
        for point in result.points:
            daily_cost = point.value.double_value
            threshold = float(os.environ.get('DAILY_COST_THRESHOLD', '50.0'))  # $50 default
            
            if daily_cost > threshold:
                send_cost_alert(daily_cost, threshold)
                break

def send_cost_alert(daily_cost, threshold):
    """Send cost alert notification."""
    from google.cloud import pubsub_v1
    
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(
        os.environ.get('GCP_PROJECT_ID'),
        'cost-alerts'
    )
    
    message = {
        'type': 'COST_ALERT',
        'daily_cost': daily_cost,
        'threshold': threshold,
        'timestamp': time.time()
    }
    
    publisher.publish(
        topic_path, 
        data=json.dumps(message).encode('utf-8')
    )
```

### Batch Processing

Implement batch processing for non-urgent tasks:

```python
def batch_process_emails(batch_size=10, max_wait_seconds=60):
    """Process emails in batches for cost efficiency."""
    from google.cloud import pubsub_v1
    
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        os.environ.get('GCP_PROJECT_ID'),
        'email-batch-subscription'
    )
    
    # Pull messages in batch
    response = subscriber.pull(
        request={
            "subscription": subscription_path,
            "max_messages": batch_size,
        }
    )
    
    if not response.received_messages:
        logging.info("No messages to process")
        return
    
    # Process messages in batch
    ack_ids = []
    emails = []
    
    for received_message in response.received_messages:
        ack_ids.append(received_message.ack_id)
        message_data = json.loads(received_message.message.data.decode('utf-8'))
        emails.append(message_data)
    
    # Process emails in parallel
    results = process_emails_batch(emails)
    
    # Acknowledge messages
    subscriber.acknowledge(
        request={
            "subscription": subscription_path,
            "ack_ids": ack_ids,
        }
    )
    
    return results
```

## Implementation Roadmap

### Phase 1: Foundation

1. **Basic Scaling Setup**
   - Increase Cloud Function memory to 512MB
   - Configure minimum instances (2-3)
   - Implement basic monitoring
   - Set up alerting for errors

2. **Performance Optimization**
   - Implement simple caching for responses
   - Optimize Pub/Sub configuration
   - Add retry logic for API calls

### Phase 2: Enhanced Scaling

1. **Multi-Region Support**
   - Deploy to secondary region
   - Implement regional failover logic
   - Set up cross-region monitoring

2. **Advanced Caching**
   - Implement Redis cache
   - Add multi-level caching strategy
   - Optimize token usage for AI responses

### Phase 3: Enterprise Features

1. **Multi-Tenant Architecture**
   - Implement tenant isolation
   - Add per-tenant configuration
   - Create tenant management API

2. **High Availability**
   - Deploy to multiple regions globally
   - Implement automated failover
   - Add circuit breakers for all external calls

3. **Cost Optimization**
   - Implement tiered processing
   - Add scheduled scaling
   - Set up detailed cost monitoring

### Phase 4: Advanced Features

1. **AI Optimization**
   - Implement model selection based on email complexity
   - Add custom fine-tuning for specific domains
   - Implement response quality monitoring

2. **Analytics and Reporting**
   - Create dashboard for system performance
   - Add response quality metrics
   - Implement user satisfaction tracking

## Conclusion

Scaling the Auto Reply Email system requires a phased approach, starting with basic optimizations and gradually implementing more advanced features. By following this guide, you can build a robust, high-performance system capable of handling enterprise workloads while maintaining cost efficiency and high availability.

For implementation assistance or custom scaling solutions, contact our support team or refer to the detailed API documentation.
    
    # Create tenant record
    tenant_id = domain.replace('.', '-')
    tenant_ref = db.collection('tenants').document(domain)
    
    tenant_data = {
        'tenant_id': tenant_id,
        'domain': domain,
        'admin_email': admin_email,
        'display_name': display_name,
        'created_at': firestore.SERVER_TIMESTAMP,
        'status': 'pending',
        'ai_model': 'gemini-1.0-pro',
        'response_tone': 'formal',
        'max_tokens': 800
    }
    
    tenant_ref.set(tenant_data)
    
    # Create initial admin user
    user_ref = db.collection('users').document(admin_email)
    user_data = {
        'email': admin_email,
        'tenant_id': tenant_id,
        'role': 'admin',
        'created_at': firestore.SERVER_TIMESTAMP,
        'status': 'active'
    }
    
    user_ref.set(user_data)
    
    # Trigger OAuth setup flow
    setup_oauth_for_tenant(tenant_id, admin_email)
    
    return tenant_id
```

## High Availability

### Multi-Region Deployment

1. **Regional Redundancy**

Configure multi-region deployment for high availability:

```terraform
# Deploy Cloud Functions to multiple regions
module "cloud_function" {
  source = "./modules/cloud_function"
  
  for_each = {
    us-central1 = { primary = true }
    us-east1    = { primary = false }
    europe-west1 = { primary = false }
  }
  
  project_id      = var.project_id
  region          = each.key
  function_name   = "auto-reply-email-${each.key}"
  is_primary      = each.value.primary
  pubsub_topic    = google_pubsub_topic.email_topic.name
  service_account = google_service_account.email_service_account.email
}

# Configure global load balancer
resource "google_compute_url_map" "url_map" {
  name            = "auto-reply-lb"
  default_service = google_compute_backend_service.backend_service.id
}

resource "google_compute_target_http_proxy" "http_proxy" {
  name    = "auto-reply-http-proxy"
  url_map = google_compute_url_map.url_map.id
}

resource "google_compute_global_forwarding_rule" "forwarding_rule" {
  name       = "auto-reply-forwarding-rule"
  target     = google_compute_target_http_proxy.http_proxy.id
  port_range = "80"
  ip_address = google_compute_global_address.lb_ip.address
}
```

2. **Cross-Region Data Replication**

Implement cross-region data replication:

```terraform
# Firestore database with multi-region configuration
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = "nam5"  # Multi-region (North America)
  type        = "FIRESTORE_NATIVE"
}

# Multi-region Cloud Storage bucket
resource "google_storage_bucket" "multi_region_bucket" {
  name          = "${var.project_id}-multi-region-storage"
  location      = "US"  # Multi-region
  storage_class = "STANDARD"
  
  versioning {
    enabled = true
  }
}
```

### Disaster Recovery

1. **Backup and Restore**

Implement automated backups:

```python
def backup_tenant_data(tenant_id):
    """Create backup of tenant data."""
    from google.cloud import firestore
    from google.cloud import storage
    import json
    import datetime
    
    # Initialize clients
    db = firestore.Client()
    storage_client = storage.Client()
    
    # Get tenant data
    tenant_data = {}
    
    # Backup tenant configuration
    tenant_ref = db.collection('tenants').document(tenant_id)
    tenant = tenant_ref.get()
    if tenant.exists:
        tenant_data['config'] = tenant.to_dict()
    
    # Backup users
    users = []
    user_docs = db.collection('users').where('tenant_id', '==', tenant_id).stream()
    for user_doc in user_docs:
        users.append(user_doc.to_dict())
    tenant_data['users'] = users
    
    # Backup response templates
    templates = []
    template_docs = db.collection('response_templates').where('tenant_id', '==', tenant_id).stream()
    for template_doc in template_docs:
        templates.append(template_doc.to_dict())
    tenant_data['templates'] = templates
    
    # Save to Cloud Storage
    bucket = storage_client.bucket(f"{os.environ.get('GCP_PROJECT_ID')}-backups")
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    blob = bucket.blob(f"tenant-backups/{tenant_id}/{timestamp}.json")
    
    blob.upload_from_string(
        json.dumps(tenant_data, default=str),
        content_type='application/json'
    )
    
    return {
        'tenant_id': tenant_id,
        'backup_time': timestamp,
        'backup_path': blob.name
    }
```

2. **Failover Mechanism**

Implement automated failover:

```python
def check_region_health(region):
    """Check health of a specific region."""
    import requests
    
    try:
        # Call health check endpoint in the region
        response = requests.get(
            f"https://{region}-{os.environ.get('GCP_PROJECT_ID')}.cloudfunctions.net/health-check",
            timeout=5
        )
        
        if response.status_code == 200 and response.json().get('status') == 'healthy':
            return True
        else:
            return False
    except Exception:
        return False

def initiate_failover(primary_region, backup_region):
    """Initiate failover from primary to backup region."""
    from google.cloud import firestore
    
    # Update global configuration
    db = firestore.Client()
    config_ref = db.collection('system_config').document('global')
    
    config_ref.update({
        'active_region': backup_region,
        'failover_timestamp': firestore.SERVER_TIMESTAMP,
        'previous_region': primary_region
    })
    
    # Update DNS/load balancer weights
    update_traffic_routing(primary_region, 0)  # 0% traffic
    update_traffic_routing(backup_region, 100)  # 100% traffic
    
    # Log failover event
    logging.critical(f"Failover initiated from {primary_region} to {backup_region}")
    
    return {
        'status': 'failover_initiated',
        'from_region': primary_region,
        'to_region': backup_region,
        'timestamp': datetime.datetime.now().isoformat()
    }
```

## Cost Optimization

### Resource Optimization

1. **Autoscaling Configuration**

Optimize autoscaling for cost efficiency:

```terraform
resource "google_cloudfunctions_function" "function" {
  # Other configuration...
  
  # Efficient autoscaling
  min_instances = 1  # Minimum to avoid cold starts
  max_instances = 50  # Maximum to control costs
}
```

2. **Tiered Processing**

Implement tiered processing based on email priority:

```python
def determine_email_priority(email_data, customer_info):
    """Determine email processing priority."""
    priority = "normal"
    
    # Check customer tier
    if customer_info and customer_info.get("tier") in ["premium", "enterprise"]:
        priority = "high"
    
    # Check for urgent keywords in subject
    urgent_keywords = ["urgent", "emergency", "critical", "immediate", "asap"]
    if any(keyword in email_data.get("subject", "").lower() for keyword in urgent_keywords):
        priority = "high"
    
    # Check for VIP senders
    vip_domains = ["important-client.com", "partner.org", "executive.net"]
    sender_domain = email_data.get("from", "").split('@')[-1]
    if sender_domain in vip_domains:
        priority = "high"
    
    return priority

def process_email_by_priority(email_data, customer_info):
    """Process email according to priority."""
    priority = determine_email_priority(email_data, customer_info)
    
    if priority == "high":
        # Use premium model with higher token limit
        model = "gemini-1.0-pro"
        max_tokens = 1000
        tone = "formal"
    else:
        # Use standard model with lower token limit
        model = "text-bison@001"  # Less expensive model
        max_tokens = 500
        tone = "friendly"
    
    # Generate response with appropriate model
    reply = generate_ai_reply(
        email_data.get("from", ""),
        email_data.get("subject", ""),
        email_data.get("body", ""),
        tone,
        customer_info,
        model=model,
        max_tokens=max_tokens
    )
    
    return reply
```

### Cost Monitoring

Implement detailed cost monitoring:

```python
def track_ai_usage_costs():
    """Track AI usage and associated costs."""
    from google.cloud import bigquery
    
    client = bigquery.Client()
    
    # Query for token usage
    query = """
        SELECT
          DATE(timestamp) as day,
          COUNT(*) as request_count,
          SUM(jsonPayload.prompt_tokens) as total_prompt_tokens,
          SUM(jsonPayload.completion_tokens) as total_completion_tokens,
          SUM(jsonPayload.total_tokens) as total_tokens
        FROM `{project_id}.{dataset}.function_logs`
        WHERE 
          timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
          AND jsonPayload.total_tokens IS NOT NULL
        GROUP BY day
        ORDER BY day DESC
    """
    
    query_job = client.query(query.format(
        project_id=os.environ.get('GCP_PROJECT_ID'),
        dataset='logs'
    ))
    results = query_job.result()
    
    # Calculate costs
    # Pricing for gemini-1.0-pro: $0.0025 per 1K prompt tokens, $0.0075 per 1K completion tokens
    cost_data = []
    for row in results:
        prompt_cost = (row.total_prompt_tokens / 1000) * 0.0025
        completion_cost = (row.total_completion_tokens / 1000) * 0.0075
        total_cost = prompt_cost + completion_cost
        
        cost_data.append({
            'day': row.day.isoformat(),
            'request_count': row.request_count,
            'prompt_tokens': row.total_prompt_tokens,
            'completion_tokens': row.total_completion_tokens,
            'total_tokens': row.total_tokens,
            'prompt_cost': prompt_cost,
            'completion_cost': completion_cost,
            'total_cost': total_cost
        })
    
    # Store cost data
    from google.cloud import firestore
    db = firestore.Client()
    
    for day_data in cost_data:
        doc_ref = db.collection('cost_tracking').document(day_data['day'])
        doc_ref.set({
            'ai_usage': day_data
        }, merge=True)
    
    return cost_data
```

## Implementation Roadmap

Follow this phased approach to scale your system:

### Phase 1: Foundation (1-2 weeks)

1. Optimize Cloud Function configuration
2. Implement basic caching
3. Set up monitoring and alerting
4. Configure proper error handling and retries

### Phase 2: Performance (2-4 weeks)

1. Implement parallel processing
2. Add multi-level caching
3. Optimize AI prompt engineering
4. Implement response time tracking

### Phase 3: Multi-Tenant (4-8 weeks)

1. Design tenant data model
2. Implement tenant isolation
3. Create tenant management API
4. Set up per-tenant OAuth flow

### Phase 4: Enterprise Scale (8-12 weeks)

1. Deploy to multiple regions
2. Implement global load balancing
3. Set up cross-region replication
4. Create disaster recovery procedures

### Phase 5: Optimization (Ongoing)

1. Implement cost tracking and optimization
2. Refine autoscaling parameters
3. Optimize AI model selection
4. Implement continuous performance monitoring

## Conclusion

Scaling the Auto Reply Email system requires a thoughtful approach to infrastructure, performance optimization, and architecture design. By following this guide, you can transform a basic system into an enterprise-grade solution capable of handling high volumes of emails while maintaining fast response times and high availability.

Remember that scaling is an iterative process. Start with the foundation, measure performance, and incrementally implement more advanced scaling strategies as your needs grow.
