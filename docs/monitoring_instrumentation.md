# Panduan Instrumentasi Pemantauan untuk Sistem Balas Email Otomatis

This guide explains how to instrument your Auto Reply Email system code to emit custom metrics for monitoring and alerting.

## Table of Contents

1. [Introduction](#introduction)
2. [Custom Metrics Overview](#custom-metrics-overview)
3. [Instrumenting Cloud Functions](#instrumenting-cloud-functions)
4. [Logging-based Metrics](#logging-based-metrics)
5. [Direct Metrics API](#direct-metrics-api)
6. [Recommended Metrics](#recommended-metrics)
7. [Integration with Monitoring Dashboard](#integration-with-monitoring-dashboard)

## Introduction

Proper instrumentation of your Auto Reply Email system enables real-time monitoring, alerting, and performance optimization. This guide covers how to add custom metrics to your Cloud Functions to track email processing rates, response times, and other key performance indicators.

## Custom Metrics Overview

Google Cloud offers two primary methods for emitting custom metrics:

1. **Logging-based metrics**: Derived from structured log entries
2. **Direct metrics**: Sent directly to the Cloud Monitoring API

Each approach has advantages:

| Method | Advantages | Disadvantages |
|--------|------------|---------------|
| Logging-based | Simple to implement, no additional libraries | Higher latency, limited metric types |
| Direct metrics | Low latency, rich metric types | Requires additional libraries, more complex |

## Instrumenting Cloud Functions

### Prerequisites

For direct metrics, add the Cloud Monitoring client library to your `requirements.txt`:

```
google-cloud-monitoring>=2.11.0
```

### Basic Instrumentation Pattern

Wrap your main function logic with instrumentation:

```python
import time
import logging
import json
from google.cloud import monitoring_v3

def process_email(event, context):
    """Cloud Function to process email notifications."""
    start_time = time.time()
    success = False
    
    try:
        # Extract email data
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        email_data = json.loads(pubsub_message)
        
        # Log the start of processing with structured data
        logging.info(
            "Starting email processing", 
            extra={
                "email_id": email_data.get("email_id", "unknown"),
                "event_type": "process_start"
            }
        )
        
        # Process the email
        result = handle_email(email_data)
        
        # Mark as successful if we get here
        success = True
        
        return result
        
    except Exception as e:
        logging.error(f"Error processing email: {str(e)}")
        raise
        
    finally:
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log metrics in structured format
        logging.info(
            "Email processing completed",
            extra={
                "email_processing_time": processing_time,
                "email_processing_success": success,
                "event_type": "process_complete"
            }
        )
        
        # Optionally, send metrics directly
        record_metrics(processing_time, success)
```

## Logging-based Metrics

### Structured Logging

Use structured logging to emit metrics that can be extracted:

```python
def log_metric(name, value, labels=None):
    """Log a metric in a structured format for Cloud Monitoring."""
    log_struct = {
        "metric_name": name,
        "metric_value": value,
        "metric_labels": labels or {}
    }
    
    logging.info(f"METRIC: {name}={value}", extra=log_struct)
```

### Example Usage

```python
# Log response time
log_metric("email_response_time", response_time_seconds, {
    "sender_domain": email_domain,
    "priority": email_priority
})

# Log success rate (0 or 1)
log_metric("email_success", 1 if success else 0)

# Log token usage
log_metric("ai_token_usage", token_count, {
    "model": model_name
})
```

### Creating Logging-based Metrics in Cloud Console

1. Go to **Logging > Logs Explorer**
2. Create a query that filters your structured logs:
   ```
   resource.type="cloud_function"
   resource.labels.function_name="process-email"
   jsonPayload.metric_name="email_response_time"
   ```
3. Click **Create Metric**
4. Configure the metric:
   - Name: `email_response_time`
   - Description: `Time taken to process and respond to an email`
   - Type: `Distribution` (for response times) or `Counter` (for counts)
   - Field name: `jsonPayload.metric_value`
   - Labels (optional): Add from `jsonPayload.metric_labels`

## Direct Metrics API

For lower latency and more metric types, use the Cloud Monitoring API directly:

```python
from google.cloud import monitoring_v3
from google.api import label_pb2 as ga_label
from google.api import metric_pb2 as ga_metric

def write_time_series(project_id, series):
    """Write a single time series to Cloud Monitoring."""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"
    client.create_time_series(name=project_name, time_series=[series])

def create_metric_descriptor(project_id, metric_type, metric_kind, value_type, description):
    """Create a custom metric descriptor."""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"
    
    descriptor = ga_metric.MetricDescriptor()
    descriptor.type = f"custom.googleapis.com/{metric_type}"
    descriptor.metric_kind = metric_kind
    descriptor.value_type = value_type
    descriptor.description = description
    
    return client.create_metric_descriptor(
        name=project_name, 
        metric_descriptor=descriptor
    )

def record_response_time(project_id, response_time, email_domain=None):
    """Record email response time metric."""
    client = monitoring_v3.MetricServiceClient()
    
    # Create the time series
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/email/response_time"
    
    if email_domain:
        series.metric.labels["email_domain"] = email_domain
    
    # Add resource (Cloud Function)
    series.resource.type = "cloud_function"
    series.resource.labels["function_name"] = "process-email"
    series.resource.labels["region"] = "us-central1"  # Replace with your region
    
    # Create a data point
    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10**9)
    
    point = series.points.add()
    point.value.double_value = response_time
    point.interval.end_time.seconds = seconds
    point.interval.end_time.nanos = nanos
    
    # Write the time series
    write_time_series(project_id, series)
```

## Recommended Metrics

| Metric Name | Type | Description | Implementation |
|-------------|------|-------------|----------------|
| `email_processing_count` | Counter | Number of emails processed | Increment on each email |
| `email_response_time` | Distribution | Time to generate and send reply | Measure start-to-finish time |
| `email_success_rate` | Gauge | Percentage of successful replies | Calculate success ratio |
| `ai_token_usage` | Counter | Number of tokens used by AI model | Count tokens per request |
| `system_health` | Gauge | Overall system health score (0-1) | Composite metric from components |
| `gmail_api_latency` | Distribution | Gmail API call latency | Measure API call duration |
| `vertex_ai_latency` | Distribution | AI model inference latency | Measure AI call duration |

### Example Implementation

```python
def record_metrics(processing_time, success, token_count=None, project_id=None):
    """Record all metrics for an email processing event."""
    project_id = project_id or os.environ.get("GCP_PROJECT_ID")
    
    try:
        # Record response time
        record_response_time(project_id, processing_time)
        
        # Record success/failure
        record_success(project_id, 1 if success else 0)
        
        # Record token usage if available
        if token_count:
            record_token_usage(project_id, token_count)
            
    except Exception as e:
        # Don't let metrics recording failure affect the main function
        logging.error(f"Failed to record metrics: {str(e)}")
```

## Integration with Monitoring Dashboard

The metrics defined in this guide integrate with the Auto Reply Email System dashboard. To ensure proper integration:

1. Use consistent metric names as defined in this guide
2. Deploy the dashboard using the `setup_monitoring.py` script
3. Verify metrics are appearing in the Cloud Monitoring console

### Custom Metric Creation Script

You can use this script to create all recommended custom metrics:

```python
def create_custom_metrics(project_id):
    """Create all custom metrics for the Auto Reply Email system."""
    from google.cloud import monitoring_v3
    from google.api import metric_pb2
    
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"
    
    # Define metrics to create
    metrics = [
        {
            "type": "email/processing_count",
            "kind": metric_pb2.MetricDescriptor.MetricKind.CUMULATIVE,
            "value_type": metric_pb2.MetricDescriptor.ValueType.INT64,
            "description": "Number of emails processed by the Auto Reply system"
        },
        {
            "type": "email/response_time",
            "kind": metric_pb2.MetricDescriptor.MetricKind.GAUGE,
            "value_type": metric_pb2.MetricDescriptor.ValueType.DOUBLE,
            "description": "Time in seconds to process and respond to an email"
        },
        {
            "type": "email/success_rate",
            "kind": metric_pb2.MetricDescriptor.MetricKind.GAUGE,
            "value_type": metric_pb2.MetricDescriptor.ValueType.DOUBLE,
            "description": "Percentage of emails successfully processed"
        },
        {
            "type": "email/ai_token_usage",
            "kind": metric_pb2.MetricDescriptor.MetricKind.CUMULATIVE,
            "value_type": metric_pb2.MetricDescriptor.ValueType.INT64,
            "description": "Number of tokens used by the AI model"
        },
        {
            "type": "system/health",
            "kind": metric_pb2.MetricDescriptor.MetricKind.GAUGE,
            "value_type": metric_pb2.MetricDescriptor.ValueType.DOUBLE,
            "description": "Overall system health score (0-1)"
        }
    ]
    
    # Create each metric
    for metric in metrics:
        descriptor = metric_pb2.MetricDescriptor()
        descriptor.type = f"custom.googleapis.com/{metric['type']}"
        descriptor.metric_kind = metric["kind"]
        descriptor.value_type = metric["value_type"]
        descriptor.description = metric["description"]
        
        try:
            client.create_metric_descriptor(
                name=project_name, 
                metric_descriptor=descriptor
            )
            print(f"Created metric: {descriptor.type}")
        except Exception as e:
            print(f"Error creating metric {descriptor.type}: {str(e)}")
```

## Conclusion

Proper instrumentation is essential for monitoring and maintaining the Auto Reply Email system. By implementing these metrics, you'll gain visibility into system performance, identify bottlenecks, and ensure timely alerts for any issues.

For assistance with monitoring setup, refer to the `setup_monitoring.py` script documentation or run the script with the `--help` flag for usage information.
