# Praktik Terbaik Keamanan untuk Sistem Balas Email Otomatis

This guide outlines comprehensive security best practices for implementing, deploying, and maintaining the Auto Reply Email system on Google Cloud Platform.

## Table of Contents

1. [Authentication and Authorization](#authentication-and-authorization)
2. [Data Protection](#data-protection)
3. [Secret Management](#secret-management)
4. [Network Security](#network-security)
5. [Monitoring and Incident Response](#monitoring-and-incident-response)
6. [Compliance Considerations](#compliance-considerations)
7. [Security Checklist](#security-checklist)

## Authentication and Authorization

### OAuth 2.0 Implementation

The system uses OAuth 2.0 for Gmail API authentication. Follow these security practices:

1. **Scope Limitation**: Request only the minimum required scopes:

```python
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
```

2. **Token Storage**: Never store OAuth tokens in code, environment variables, or logs:

```python
# INCORRECT - Don't do this
os.environ["GMAIL_TOKEN"] = token_json

# CORRECT - Use Secret Manager
from google.cloud import secretmanager
secret_client = secretmanager.SecretManagerServiceClient()
secret_client.add_secret_version(
    request={
        "parent": f"projects/{project_id}/secrets/gmail-oauth-token",
        "payload": {"data": token_json.encode("UTF-8")},
    }
)
```

3. **Token Refresh**: Implement secure token refresh with proper error handling:

```python
def refresh_token_if_needed(credentials):
    """Refresh OAuth token if expired."""
    if credentials.expired:
        try:
            credentials.refresh(Request())
            # Update stored token securely
            update_stored_token(credentials.to_json())
            logging.info("OAuth token refreshed successfully")
        except Exception as e:
            logging.error(f"Token refresh failed: {str(e)}")
            raise
```

4. **Consent Screen Security**: Configure the OAuth consent screen with:
   - Verified domain
   - Clear application name and description
   - Accurate privacy policy URL
   - Limited authorized domains

### Service Account Management

1. **Principle of Least Privilege**: Assign only necessary IAM roles:

```terraform
resource "google_service_account" "email_service_account" {
  account_id   = "auto-reply-email-sa"
  display_name = "Auto Reply Email Service Account"
}

resource "google_project_iam_member" "pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.email_service_account.email}"
}

resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.email_service_account.email}"
}

resource "google_project_iam_member" "secretmanager_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.email_service_account.email}"
}
```

2. **Key Management**: Avoid downloading service account keys. Use workload identity or attached service accounts:

```terraform
resource "google_cloudfunctions_function" "function" {
  name        = "auto-reply-email"
  # Other configuration...
  
  service_account_email = google_service_account.email_service_account.email
}
```

3. **Regular Auditing**: Implement regular audits of service account permissions:

```bash
# Add to your Makefile
audit-permissions:
	@echo "Auditing service account permissions..."
	@gcloud projects get-iam-policy $(GCP_PROJECT_ID) \
		--format=json | jq '.bindings[] | select(.members[] | contains("auto-reply-email-sa"))'
```

## Data Protection

### Email Content Security

1. **Data Minimization**: Process only necessary email data:

```python
def extract_minimal_email_data(message):
    """Extract only necessary data from email message."""
    headers = {h['name'].lower(): h['value'] for h in message['payload']['headers']}
    
    # Extract only needed fields
    return {
        "message_id": message['id'],
        "thread_id": message.get('threadId', ''),
        "subject": headers.get('subject', ''),
        "from": headers.get('from', ''),
        "body": extract_email_body(message),
        # Don't extract CC, BCC, or other sensitive fields unless required
    }
```

2. **Content Filtering**: Implement content filtering to prevent data leakage:

```python
def sanitize_email_content(content):
    """Sanitize email content to remove sensitive information."""
    # Remove potential PII patterns
    patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
        r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',   # SSN
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Emails
    ]
    
    sanitized = content
    for pattern in patterns:
        sanitized = re.sub(pattern, '[REDACTED]', sanitized)
    
    return sanitized
```

3. **Email Storage**: Avoid unnecessary storage of email content:

```python
def process_email_without_storage(email_data):
    """Process email without storing full content."""
    try:
        # Process in memory
        customer_info = verify_customer(email_data.get("from", ""))
        reply = generate_ai_reply(
            email_data.get("from", ""),
            email_data.get("subject", ""),
            email_data.get("body", ""),
            "formal",
            customer_info
        )
        
        # Send reply
        success = send_reply(
            service,
            email_data.get("from", ""),
            email_data.get("subject", ""),
            reply
        )
        
        # Only log metadata, not content
        logging.info(f"Processed email {email_data.get('message_id')} from {mask_email(email_data.get('from', ''))}")
        
        return success
    finally:
        # Explicitly clear sensitive data
        if 'email_data' in locals():
            email_data.clear()
```

### Data in Transit

1. **TLS Enforcement**: Ensure all API communications use TLS 1.2+:

```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

class TLSAdapter(HTTPAdapter):
    """Adapter that ensures TLS 1.2+ is used."""
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ssl_version=ssl.PROTOCOL_TLS)
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount('https://', TLSAdapter())
```

2. **VPC Service Controls**: Implement VPC Service Controls to restrict API access:

```terraform
resource "google_access_context_manager_service_perimeter" "perimeter" {
  name         = "accessPolicies/${google_access_context_manager_access_policy.policy.name}/servicePerimeters/auto_reply_perimeter"
  title        = "Auto Reply Email Perimeter"
  perimeter_type = "PERIMETER_TYPE_REGULAR"
  
  status {
    restricted_services = [
      "aiplatform.googleapis.com",
      "secretmanager.googleapis.com",
      "pubsub.googleapis.com"
    ]
    
    vpc_accessible_services {
      enable_restriction = true
      allowed_services   = ["RESTRICTED-SERVICES"]
    }
    
    ingress_policies {
      ingress_from {
        identity_type = "ANY_IDENTITY"
        sources {
          resource = "projects/${var.project_id}"
        }
      }
      ingress_to {
        resources = ["*"]
        operations {
          service_name = "*"
        }
      }
    }
  }
}
```

### Data at Rest

1. **CMEK (Customer-Managed Encryption Keys)**: Use CMEK for sensitive data:

```terraform
resource "google_kms_key_ring" "keyring" {
  name     = "auto-reply-keyring"
  location = var.region
}

resource "google_kms_crypto_key" "key" {
  name     = "auto-reply-key"
  key_ring = google_kms_key_ring.keyring.id
  rotation_period = "7776000s"  # 90 days
}

resource "google_secret_manager_secret" "gmail_token" {
  secret_id = "gmail-oauth-token"
  
  replication {
    user_managed {
      replicas {
        location = var.region
        customer_managed_encryption {
          kms_key_name = google_kms_crypto_key.key.id
        }
      }
    }
  }
}
```

2. **Secure Cloud Function Environment**: Ensure Cloud Function environment is secure:

```terraform
resource "google_cloudfunctions_function" "function" {
  # Other configuration...
  
  # Enforce HTTPS
  https_trigger_security_level = "SECURE_ALWAYS"
  
  # Use latest runtime
  runtime = "python310"
  
  # Enforce ingress settings
  ingress_settings = "ALLOW_INTERNAL_ONLY"
  
  # Enable CMEK if available
  kms_key_name = google_kms_crypto_key.key.id
}
```

## Secret Management

### Secure Secret Handling

1. **Secret Manager Integration**: Use Secret Manager for all credentials:

```python
def get_secret(secret_id):
    """Retrieve a secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{os.environ.get('GCP_PROJECT_ID')}/secrets/{secret_id}/versions/latest"
    
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logging.error(f"Error retrieving secret {secret_id}: {str(e)}")
        raise
```

2. **Secret Rotation**: Implement regular secret rotation:

```python
def rotate_oauth_token():
    """Rotate OAuth token on a schedule."""
    # Get current credentials
    credentials_json = get_secret("gmail-oauth-token")
    credentials = Credentials.from_json(credentials_json)
    
    # Force token refresh
    credentials.refresh(Request())
    
    # Update secret with new token
    client = secretmanager.SecretManagerServiceClient()
    parent = client.secret_path(os.environ.get("GCP_PROJECT_ID"), "gmail-oauth-token")
    
    client.add_secret_version(
        request={
            "parent": parent,
            "payload": {"data": credentials.to_json().encode("UTF-8")},
        }
    )
    
    logging.info("OAuth token rotated successfully")
```

3. **Secret Access Auditing**: Enable audit logs for secret access:

```terraform
resource "google_project_iam_audit_config" "audit_config" {
  project = var.project_id
  service = "secretmanager.googleapis.com"
  
  audit_log_config {
    log_type = "DATA_READ"
  }
  
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}
```

## Network Security

### Secure Communication

1. **Private Google Access**: Use Private Google Access for API calls:

```terraform
resource "google_compute_network" "vpc" {
  name                    = "auto-reply-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "auto-reply-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
  
  # Enable Private Google Access
  private_ip_google_access = true
}

resource "google_vpc_access_connector" "connector" {
  name          = "auto-reply-vpc-connector"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.name
}

resource "google_cloudfunctions_function" "function" {
  # Other configuration...
  
  vpc_connector = google_vpc_access_connector.connector.id
  vpc_connector_egress_settings = "PRIVATE_RANGES_ONLY"
}
```

2. **Firewall Rules**: Implement restrictive firewall rules:

```terraform
resource "google_compute_firewall" "internal_only" {
  name    = "auto-reply-internal-only"
  network = google_compute_network.vpc.name
  
  deny {
    protocol = "all"
  }
  
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["auto-reply-function"]
  
  # Allow only necessary connections
  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
  
  source_ranges = [
    "35.199.192.0/19",  # Google Cloud Functions
    "35.235.240.0/20"   # Google Cloud IAP
  ]
}
```

### API Security

1. **API Request Validation**: Validate all API requests:

```python
def validate_pubsub_message(event):
    """Validate Pub/Sub message structure and content."""
    if not event or not event.get('data'):
        logging.error("Invalid Pub/Sub message: missing data")
        return False
    
    try:
        message_data = json.loads(base64.b64decode(event['data']).decode('utf-8'))
        
        # Validate required fields
        required_fields = ['historyId', 'emailAddress']
        for field in required_fields:
            if field not in message_data:
                logging.error(f"Invalid Pub/Sub message: missing {field}")
                return False
        
        # Validate data types
        if not isinstance(message_data['historyId'], str):
            logging.error("Invalid historyId type")
            return False
            
        if not isinstance(message_data['emailAddress'], str):
            logging.error("Invalid emailAddress type")
            return False
        
        return True
    except Exception as e:
        logging.error(f"Error validating Pub/Sub message: {str(e)}")
        return False
```

2. **Rate Limiting**: Implement rate limiting for API calls:

```python
class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period  # in seconds
        self.calls = []
        self.lock = threading.Lock()
    
    def acquire(self):
        """Acquire permission to make an API call."""
        with self.lock:
            now = time.time()
            
            # Remove expired timestamps
            self.calls = [t for t in self.calls if now - t < self.period]
            
            if len(self.calls) >= self.max_calls:
                return False
            
            self.calls.append(now)
            return True

# Usage
gmail_limiter = RateLimiter(max_calls=100, period=60)  # 100 calls per minute
vertex_limiter = RateLimiter(max_calls=60, period=60)  # 60 calls per minute

def rate_limited_api_call(limiter, func, *args, **kwargs):
    """Make a rate-limited API call."""
    if not limiter.acquire():
        time.sleep(1)  # Wait before retry
        return rate_limited_api_call(limiter, func, *args, **kwargs)
    
    return func(*args, **kwargs)
```

## Monitoring and Incident Response

### Security Monitoring

1. **Cloud Security Command Center**: Enable Cloud Security Command Center:

```terraform
resource "google_project_service" "scc_api" {
  project = var.project_id
  service = "securitycenter.googleapis.com"
}

resource "google_scc_source" "custom_source" {
  display_name = "Auto Reply Email Security"
  description  = "Security monitoring for Auto Reply Email system"
  organization = var.organization_id
}
```

2. **Custom Security Alerts**: Set up security-specific alerts:

```python
def create_security_alerts():
    """Create security-specific alerts."""
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{os.environ.get('GCP_PROJECT_ID')}"
    
    # Alert for unusual access patterns
    unusual_access_alert = {
        "display_name": "Unusual Secret Access Pattern",
        "combiner": monitoring_v3.AlertPolicy.Combiner.OR,
        "conditions": [
            {
                "display_name": "High Secret Access Rate",
                "condition_threshold": {
                    "filter": 'resource.type="secretmanager_secret" AND metric.type="secretmanager.googleapis.com/secret/access_count"',
                    "comparison": monitoring_v3.ComparisonType.COMPARISON_GT,
                    "threshold_value": 100,
                    "duration": {"seconds": 300},  # 5 minutes
                    "trigger": {"count": 1},
                }
            }
        ],
        "notification_channels": [notification_channel],
        "documentation": {
            "content": "Unusual number of secret accesses detected. This may indicate credential theft or misuse.",
            "mime_type": "text/markdown",
        },
    }
    
    client.create_alert_policy(name=project_name, alert_policy=unusual_access_alert)
```

3. **Audit Logging**: Enable comprehensive audit logging:

```terraform
resource "google_project_iam_audit_config" "project" {
  project = var.project_id
  service = "allServices"
  
  audit_log_config {
    log_type = "ADMIN_READ"
  }
  
  audit_log_config {
    log_type = "DATA_READ"
  }
  
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}
```

### Incident Response

1. **Automated Response**: Implement automated incident response:

```python
def handle_security_incident(incident_type, details):
    """Handle security incidents with automated response."""
    logging.critical(f"Security incident detected: {incident_type}")
    
    # Record incident details
    incident_id = str(uuid.uuid4())
    
    # Take immediate action based on incident type
    if incident_type == "unauthorized_access":
        # Revoke suspicious tokens
        revoke_token(details.get("token_id"))
        
    elif incident_type == "data_exfiltration":
        # Temporarily disable the function
        disable_cloud_function()
    
    # Notify security team
    notify_security_team(incident_id, incident_type, details)
    
    return incident_id
```

2. **Incident Playbooks**: Create security incident playbooks:

```markdown
# Security Incident Response Playbook

## Unauthorized Access Incident

1. **Identification**:
   - Alert triggered from Cloud Security Command Center
   - Unusual access patterns in audit logs
   - Failed authentication attempts

2. **Containment**:
   - Revoke affected OAuth tokens
   - Rotate service account keys
   - Temporarily restrict access to affected resources

3. **Eradication**:
   - Identify root cause of the breach
   - Remove any unauthorized access
   - Patch vulnerabilities

4. **Recovery**:
   - Generate new OAuth tokens
   - Restore normal operation
   - Verify system integrity

5. **Lessons Learned**:
   - Document incident details
   - Update security controls
   - Conduct team review
```

## Compliance Considerations

### Data Privacy

1. **GDPR Compliance**: Implement GDPR-compliant data handling:

```python
def process_with_gdpr_compliance(email_data):
    """Process email with GDPR compliance in mind."""
    # Extract only necessary data
    minimal_data = extract_minimal_data(email_data)
    
    # Process with explicit purpose
    result = process_for_customer_service(minimal_data)
    
    # Delete data after processing
    delete_sensitive_data(minimal_data)
    
    return result

def delete_sensitive_data(data_dict):
    """Securely delete sensitive data."""
    for key in list(data_dict.keys()):
        if isinstance(data_dict[key], str):
            # Overwrite strings with zeros
            data_dict[key] = '0' * len(data_dict[key])
        elif isinstance(data_dict[key], dict):
            delete_sensitive_data(data_dict[key])
    
    # Clear the dictionary
    data_dict.clear()
```

2. **Data Retention Policy**: Implement proper data retention:

```python
def implement_retention_policy():
    """Implement data retention policy for logs and temporary data."""
    # Configure log retention
    client = logging_v2.ConfigServiceV2Client()
    
    # Set retention for 30 days
    sink_name = client.sink_path(os.environ.get("GCP_PROJECT_ID"), "auto-reply-logs")
    sink = {
        "name": sink_name,
        "filter": 'resource.type="cloud_function" AND resource.labels.function_name="auto-reply-email"',
        "destination": f"storage.googleapis.com/{os.environ.get('GCP_PROJECT_ID')}-logs",
        "output_version_format": logging_v2.LogSink.VersionFormat.V2,
    }
    
    client.update_sink(sink=sink)
    
    # Set up scheduled cleanup job
    scheduler_client = scheduler_v1.CloudSchedulerClient()
    parent = scheduler_client.location_path(os.environ.get("GCP_PROJECT_ID"), os.environ.get("GCP_REGION"))
    
    job = {
        "name": f"{parent}/jobs/cleanup-temp-data",
        "description": "Clean up temporary data according to retention policy",
        "schedule": "0 0 * * *",  # Daily at midnight
        "time_zone": "UTC",
        "http_target": {
            "uri": f"https://{os.environ.get('GCP_REGION')}-{os.environ.get('GCP_PROJECT_ID')}.cloudfunctions.net/cleanup-data",
            "http_method": scheduler_v1.HttpMethod.POST,
        },
    }
    
    scheduler_client.create_job(parent=parent, job=job)
```

### Security Compliance

1. **Security Controls Documentation**: Document security controls:

```markdown
# Security Controls Documentation

## Access Controls
- **IAM Roles**: Least privilege principle implemented
- **Authentication**: OAuth 2.0 with secure token storage
- **Authorization**: Service account with minimal permissions

## Data Protection
- **Encryption in Transit**: TLS 1.2+ for all communications
- **Encryption at Rest**: CMEK for Secret Manager and Cloud Storage
- **Data Minimization**: Processing only required email fields

## Monitoring
- **Audit Logging**: Comprehensive logging for all services
- **Alerts**: Real-time alerts for security events
- **Incident Response**: Documented procedures for security incidents

## Compliance
- **GDPR**: Compliant data handling procedures
- **Data Retention**: 30-day retention policy
- **Privacy**: No unnecessary PII storage
```

2. **Compliance Scanning**: Implement regular compliance scanning:

```python
def run_compliance_scan():
    """Run automated compliance scan."""
    # Check for security misconfigurations
    check_iam_permissions()
    check_encryption_settings()
    check_network_security()
    
    # Validate data handling practices
    validate_data_retention()
    validate_pii_handling()
    
    # Generate compliance report
    generate_compliance_report()

def check_iam_permissions():
    """Check for overly permissive IAM roles."""
    client = resourcemanager_v3.ProjectsClient()
    policy = client.get_iam_policy(resource=f"projects/{os.environ.get('GCP_PROJECT_ID')}")
    
    issues = []
    for binding in policy.bindings:
        # Check for overly permissive roles
        if binding.role in ["roles/owner", "roles/editor"]:
            issues.append(f"Overly permissive role {binding.role} assigned")
        
        # Check for public access
        if "allUsers" in binding.members or "allAuthenticatedUsers" in binding.members:
            issues.append(f"Public access granted through {binding.role}")
    
    return issues
```

## Security Checklist

Use this checklist to ensure your Auto Reply Email system meets security requirements:

### Pre-Deployment Security Checklist

- [ ] **Authentication**
  - [ ] OAuth scopes limited to minimum required
  - [ ] Service accounts follow least privilege principle
  - [ ] No hardcoded credentials in code
  - [ ] Secure token storage implemented

- [ ] **Data Protection**
  - [ ] Email content minimized to necessary fields
  - [ ] No persistent storage of email content
  - [ ] TLS 1.2+ enforced for all communications
  - [ ] CMEK implemented for sensitive data

- [ ] **Secret Management**
  - [ ] All secrets stored in Secret Manager
  - [ ] Secret rotation process implemented
  - [ ] Secret access auditing enabled

- [ ] **Network Security**
  - [ ] VPC Service Controls configured
  - [ ] Private Google Access enabled
  - [ ] Restrictive firewall rules implemented
  - [ ] Ingress settings limited to internal only

- [ ] **Monitoring**
  - [ ] Audit logging enabled for all services
  - [ ] Security-specific alerts configured
  - [ ] Incident response playbooks created

- [ ] **Compliance**
  - [ ] GDPR-compliant data handling implemented
  - [ ] Data retention policy defined
  - [ ] Security controls documented

### Regular Security Maintenance

- [ ] **Weekly**
  - [ ] Review security logs for unusual patterns
  - [ ] Check alert notifications
  - [ ] Verify function permissions

- [ ] **Monthly**
  - [ ] Rotate OAuth tokens
  - [ ] Run compliance scan
  - [ ] Update security documentation

- [ ] **Quarterly**
  - [ ] Conduct security review
  - [ ] Test incident response procedures
  - [ ] Update security controls as needed

## Conclusion

Implementing these security best practices will help ensure your Auto Reply Email system protects sensitive data, maintains compliance, and prevents unauthorized access. Security should be an ongoing process, with regular reviews and updates to address emerging threats and changing requirements.

## AI Privacy Controls (v2.1.0)

- **Per-email chat isolation**: Initialize Vertex AI chat with `start_chat(history=[])` for setiap email untuk mencegah kebocoran memori lintas pelanggan/thread.
- **Strip quoted history**: Hapus teks kutipan/riwayat dari body sebelum dikirim ke AI agar konteks terbatas pada email aktif.
- **Output sanitization**: Redaksi alamat email selain `addhe.warman+cs@gmail.com` dan deretan digit panjang (PII seperti nomor identitas/akun) dari output AI.
- **Reply-To alias enforcement**: Set `From` dan `Reply-To` ke `addhe.warman+cs@gmail.com` untuk memastikan balasan masuk melalui jalur alias yang dilindungi.
- **Scope minimization**: Hanya kirimkan field yang diperlukan (subject, potongan body terpilih) ke AI; hindari metadata sensitif yang tidak perlu.
