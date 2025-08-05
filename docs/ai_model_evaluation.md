# AI Model Evaluation Guide for Auto Reply Email System

This guide provides methodologies and best practices for evaluating and optimizing the AI models used in the Auto Reply Email system.

## Table of Contents

1. [Evaluation Framework](#evaluation-framework)
2. [Quantitative Metrics](#quantitative-metrics)
3. [Qualitative Assessment](#qualitative-assessment)
4. [A/B Testing](#ab-testing)
5. [Model Comparison](#model-comparison)
6. [Continuous Improvement](#continuous-improvement)

## Evaluation Framework

A comprehensive evaluation framework should assess both technical performance and business value:

### Key Dimensions

1. **Response Quality**: Accuracy, relevance, and helpfulness of AI-generated replies
2. **Response Time**: Speed of generating and sending replies
3. **User Satisfaction**: Customer perception of AI responses
4. **Business Impact**: Efficiency gains and cost savings

### Evaluation Process

1. **Baseline Establishment**: Document current performance metrics
2. **Regular Assessment**: Schedule weekly or monthly evaluations
3. **Feedback Loop**: Incorporate findings into model improvements
4. **Documentation**: Maintain evaluation history for trend analysis

## Quantitative Metrics

### Technical Performance Metrics

1. **Response Time Metrics**

```python
def measure_response_times():
    """Measure and analyze AI response generation times."""
    query = """
        SELECT
          TIMESTAMP_TRUNC(timestamp, HOUR) as hour,
          COUNT(*) as request_count,
          AVG(jsonPayload.ai_generation_time) as avg_generation_time,
          APPROX_QUANTILES(jsonPayload.ai_generation_time, 100)[OFFSET(50)] as median_generation_time,
          APPROX_QUANTILES(jsonPayload.ai_generation_time, 100)[OFFSET(95)] as p95_generation_time,
          APPROX_QUANTILES(jsonPayload.ai_generation_time, 100)[OFFSET(99)] as p99_generation_time
        FROM `{project_id}.{dataset}.function_logs`
        WHERE 
          timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
          AND jsonPayload.ai_generation_time IS NOT NULL
        GROUP BY hour
        ORDER BY hour DESC
    """
    
    # Execute query using BigQuery client
    client = bigquery.Client()
    query_job = client.query(query)
    results = query_job.result()
    
    # Process and visualize results
    times = []
    for row in results:
        times.append({
            'hour': row.hour,
            'count': row.request_count,
            'avg': row.avg_generation_time,
            'median': row.median_generation_time,
            'p95': row.p95_generation_time,
            'p99': row.p99_generation_time
        })
    
    return times
```

2. **Error Rate Analysis**

```python
def analyze_error_rates():
    """Analyze AI response error rates by category."""
    query = """
        SELECT
          DATE(timestamp) as day,
          jsonPayload.error_type,
          COUNT(*) as error_count
        FROM `{project_id}.{dataset}.function_logs`
        WHERE 
          timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
          AND jsonPayload.error_type IS NOT NULL
        GROUP BY day, jsonPayload.error_type
        ORDER BY day DESC, error_count DESC
    """
    
    # Execute query using BigQuery client
    client = bigquery.Client()
    query_job = client.query(query)
    results = query_job.result()
    
    # Process results
    error_data = {}
    for row in results:
        if row.day not in error_data:
            error_data[row.day] = {}
        error_data[row.day][row.error_type] = row.error_count
    
    return error_data
```

3. **Token Usage Efficiency**

```python
def analyze_token_usage():
    """Analyze token usage efficiency."""
    query = """
        SELECT
          DATE(timestamp) as day,
          AVG(jsonPayload.prompt_tokens) as avg_prompt_tokens,
          AVG(jsonPayload.completion_tokens) as avg_completion_tokens,
          AVG(jsonPayload.total_tokens) as avg_total_tokens,
          SUM(jsonPayload.total_tokens) as total_tokens_used
        FROM `{project_id}.{dataset}.function_logs`
        WHERE 
          timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
          AND jsonPayload.total_tokens IS NOT NULL
        GROUP BY day
        ORDER BY day DESC
    """
    
    # Execute query
    client = bigquery.Client()
    query_job = client.query(query)
    results = query_job.result()
    
    # Process results
    token_data = []
    for row in results:
        token_data.append({
            'day': row.day,
            'avg_prompt_tokens': row.avg_prompt_tokens,
            'avg_completion_tokens': row.avg_completion_tokens,
            'avg_total_tokens': row.avg_total_tokens,
            'total_tokens_used': row.total_tokens_used
        })
    
    return token_data
```

### Business Performance Metrics

1. **Response Rate Tracking**

```python
def track_response_rates():
    """Track email response rates over time."""
    # Query for emails received and responses sent
    received_query = """
        SELECT
          DATE(timestamp) as day,
          COUNT(*) as emails_received
        FROM `{project_id}.{dataset}.gmail_watch_events`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY day
        ORDER BY day DESC
    """
    
    responses_query = """
        SELECT
          DATE(timestamp) as day,
          COUNT(*) as responses_sent
        FROM `{project_id}.{dataset}.function_logs`
        WHERE 
          timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
          AND jsonPayload.response_sent = true
        GROUP BY day
        ORDER BY day DESC
    """
    
    # Execute queries
    client = bigquery.Client()
    received_results = client.query(received_query).result()
    response_results = client.query(responses_query).result()
    
    # Process results
    received_data = {row.day: row.emails_received for row in received_results}
    response_data = {row.day: row.responses_sent for row in response_results}
    
    # Calculate response rates
    response_rates = {}
    for day in received_data:
        if day in response_data:
            response_rates[day] = response_data[day] / received_data[day]
    
    return response_rates
```

2. **Cost Analysis**

```python
def calculate_cost_metrics():
    """Calculate cost metrics for AI responses."""
    # Token usage query
    token_query = """
        SELECT
          DATE(timestamp) as day,
          SUM(jsonPayload.prompt_tokens) as total_prompt_tokens,
          SUM(jsonPayload.completion_tokens) as total_completion_tokens
        FROM `{project_id}.{dataset}.function_logs`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY day
        ORDER BY day DESC
    """
    
    # Execute query
    client = bigquery.Client()
    results = client.query(token_query).result()
    
    # Process results with pricing
    # Pricing for gemini-1.0-pro: $0.0025 per 1K prompt tokens, $0.0075 per 1K completion tokens
    cost_data = []
    for row in results:
        prompt_cost = (row.total_prompt_tokens / 1000) * 0.0025
        completion_cost = (row.total_completion_tokens / 1000) * 0.0075
        total_cost = prompt_cost + completion_cost
        
        cost_data.append({
            'day': row.day,
            'prompt_cost': prompt_cost,
            'completion_cost': completion_cost,
            'total_cost': total_cost
        })
    
    return cost_data
```

## Qualitative Assessment

### Human Evaluation Framework

1. **Evaluation Rubric**

Create a standardized rubric for human evaluators:

| Dimension | 1 (Poor) | 2 (Fair) | 3 (Good) | 4 (Very Good) | 5 (Excellent) |
|-----------|----------|----------|----------|---------------|---------------|
| **Relevance** | Response doesn't address the query | Partially addresses the query | Addresses the main query but misses details | Addresses query with most details | Completely addresses all aspects of the query |
| **Accuracy** | Contains multiple factual errors | Contains minor factual errors | Mostly accurate with small omissions | Highly accurate with minimal issues | Completely accurate information |
| **Tone** | Inappropriate tone for context | Somewhat inappropriate tone | Acceptable tone | Appropriate professional tone | Perfect tone for context and recipient |
| **Clarity** | Confusing and unclear | Somewhat unclear | Reasonably clear | Very clear and well-structured | Exceptionally clear and well-organized |
| **Helpfulness** | Not helpful | Minimally helpful | Moderately helpful | Very helpful | Extremely helpful and goes beyond expectations |

2. **Evaluation Process Implementation**

```python
def implement_human_evaluation(sample_size=50):
    """Implement human evaluation process for AI responses."""
    # Select random sample of responses
    query = """
        SELECT
          jsonPayload.message_id,
          jsonPayload.from_email,
          jsonPayload.subject,
          jsonPayload.original_email,
          jsonPayload.ai_response
        FROM `{project_id}.{dataset}.function_logs`
        WHERE 
          timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
          AND jsonPayload.ai_response IS NOT NULL
        ORDER BY RAND()
        LIMIT {sample_size}
    """
    
    # Execute query
    client = bigquery.Client()
    results = client.query(query).result()
    
    # Prepare evaluation data
    evaluation_data = []
    for row in results:
        evaluation_data.append({
            'message_id': row.message_id,
            'from_email': row.from_email,
            'subject': row.subject,
            'original_email': row.original_email,
            'ai_response': row.ai_response,
            'evaluation_url': generate_evaluation_url(row.message_id)
        })
    
    # Send to evaluators
    send_evaluation_requests(evaluation_data)
    
    return len(evaluation_data)
```

### Automated Quality Metrics

1. **Sentiment Analysis**

```python
def analyze_response_sentiment():
    """Analyze sentiment of AI responses."""
    # Get recent responses
    query = """
        SELECT
          jsonPayload.message_id,
          jsonPayload.ai_response
        FROM `{project_id}.{dataset}.function_logs`
        WHERE 
          timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
          AND jsonPayload.ai_response IS NOT NULL
        LIMIT 1000
    """
    
    # Execute query
    client = bigquery.Client()
    results = client.query(query).result()
    
    # Analyze sentiment
    from google.cloud import language_v1
    language_client = language_v1.LanguageServiceClient()
    
    sentiment_scores = []
    for row in results:
        document = language_v1.Document(
            content=row.ai_response,
            type_=language_v1.Document.Type.PLAIN_TEXT
        )
        sentiment = language_client.analyze_sentiment(document=document).document_sentiment
        
        sentiment_scores.append({
            'message_id': row.message_id,
            'score': sentiment.score,
            'magnitude': sentiment.magnitude
        })
    
    return sentiment_scores
```

2. **Readability Assessment**

```python
def assess_readability():
    """Assess readability of AI responses."""
    # Get recent responses
    query = """
        SELECT
          jsonPayload.message_id,
          jsonPayload.ai_response
        FROM `{project_id}.{dataset}.function_logs`
        WHERE 
          timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
          AND jsonPayload.ai_response IS NOT NULL
        LIMIT 1000
    """
    
    # Execute query
    client = bigquery.Client()
    results = client.query(query).result()
    
    # Calculate readability metrics
    import textstat
    
    readability_scores = []
    for row in results:
        readability_scores.append({
            'message_id': row.message_id,
            'flesch_reading_ease': textstat.flesch_reading_ease(row.ai_response),
            'flesch_kincaid_grade': textstat.flesch_kincaid_grade(row.ai_response),
            'smog_index': textstat.smog_index(row.ai_response),
            'coleman_liau_index': textstat.coleman_liau_index(row.ai_response),
            'automated_readability_index': textstat.automated_readability_index(row.ai_response)
        })
    
    return readability_scores
```

## A/B Testing

### Testing Framework

1. **Test Configuration**

```python
def configure_ab_test(test_name, description, variants, distribution):
    """Configure an A/B test for AI response generation."""
    # Create test configuration
    test_config = {
        'test_name': test_name,
        'description': description,
        'start_time': datetime.datetime.now().isoformat(),
        'variants': variants,
        'distribution': distribution,
        'status': 'active'
    }
    
    # Store configuration in Firestore
    db = firestore.Client()
    db.collection('ab_tests').document(test_name).set(test_config)
    
    return test_config
```

2. **Variant Selection**

```python
def select_variant(test_name, email_id):
    """Select a variant for a specific email based on test configuration."""
    # Get test configuration
    db = firestore.Client()
    test_config = db.collection('ab_tests').document(test_name).get().to_dict()
    
    if not test_config or test_config.get('status') != 'active':
        return 'default'
    
    # Deterministic variant selection based on email_id
    import hashlib
    hash_value = int(hashlib.md5(email_id.encode()).hexdigest(), 16)
    normalized_hash = hash_value / 2**128  # Normalize to [0, 1)
    
    # Select variant based on distribution
    cumulative = 0
    for variant, weight in test_config['distribution'].items():
        cumulative += weight
        if normalized_hash < cumulative:
            # Record assignment
            db.collection('ab_test_assignments').add({
                'test_name': test_name,
                'email_id': email_id,
                'variant': variant,
                'timestamp': datetime.datetime.now()
            })
            return variant
    
    return list(test_config['distribution'].keys())[0]  # Fallback
```

3. **Results Analysis**

```python
def analyze_ab_test_results(test_name):
    """Analyze results of an A/B test."""
    # Get test configuration
    db = firestore.Client()
    test_config = db.collection('ab_tests').document(test_name).get().to_dict()
    
    if not test_config:
        return {'error': 'Test not found'}
    
    # Get assignments
    assignments = db.collection('ab_test_assignments').where('test_name', '==', test_name).stream()
    assignment_map = {}
    for assignment in assignments:
        data = assignment.to_dict()
        assignment_map[data['email_id']] = data['variant']
    
    # Get metrics for each assignment
    metrics_query = """
        SELECT
          jsonPayload.message_id,
          jsonPayload.response_time,
          jsonPayload.total_tokens,
          jsonPayload.customer_reply
        FROM `{project_id}.{dataset}.function_logs`
        WHERE jsonPayload.message_id IN UNNEST(@message_ids)
    """
    
    client = bigquery.Client()
    query_job = client.query(
        metrics_query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayParameter('message_ids', 'STRING', list(assignment_map.keys()))
            ]
        )
    )
    results = query_job.result()
    
    # Aggregate results by variant
    variant_metrics = {variant: {
        'count': 0,
        'response_time': [],
        'token_usage': [],
        'customer_replies': 0
    } for variant in test_config['variants']}
    
    for row in results:
        variant = assignment_map.get(row.message_id)
        if variant in variant_metrics:
            variant_metrics[variant]['count'] += 1
            variant_metrics[variant]['response_time'].append(row.response_time)
            variant_metrics[variant]['token_usage'].append(row.total_tokens)
            if row.customer_reply:
                variant_metrics[variant]['customer_replies'] += 1
    
    # Calculate statistics
    for variant, metrics in variant_metrics.items():
        if metrics['count'] > 0:
            metrics['avg_response_time'] = sum(metrics['response_time']) / len(metrics['response_time'])
            metrics['avg_token_usage'] = sum(metrics['token_usage']) / len(metrics['token_usage'])
            metrics['reply_rate'] = metrics['customer_replies'] / metrics['count']
    
    return variant_metrics
```

## Model Comparison

### Comparison Framework

1. **Model Evaluation Setup**

```python
def setup_model_comparison(models, evaluation_metrics):
    """Set up a structured comparison between different AI models."""
    # Create comparison configuration
    comparison_id = str(uuid.uuid4())
    comparison_config = {
        'id': comparison_id,
        'models': models,
        'metrics': evaluation_metrics,
        'start_time': datetime.datetime.now().isoformat(),
        'status': 'active',
        'results': {}
    }
    
    # Store configuration
    db = firestore.Client()
    db.collection('model_comparisons').document(comparison_id).set(comparison_config)
    
    return comparison_id
```

2. **Parallel Model Evaluation**

```python
def evaluate_models_on_sample(comparison_id, sample_size=100):
    """Evaluate multiple models on the same email sample."""
    # Get comparison configuration
    db = firestore.Client()
    comparison = db.collection('model_comparisons').document(comparison_id).get().to_dict()
    
    if not comparison or comparison.get('status') != 'active':
        return {'error': 'Invalid comparison'}
    
    # Get email sample
    query = """
        SELECT
          jsonPayload.message_id,
          jsonPayload.from_email,
          jsonPayload.subject,
          jsonPayload.original_email
        FROM `{project_id}.{dataset}.function_logs`
        WHERE jsonPayload.original_email IS NOT NULL
        ORDER BY RAND()
        LIMIT {sample_size}
    """
    
    client = bigquery.Client()
    query_job = client.query(query.format(
        project_id=os.environ.get('GCP_PROJECT_ID'),
        dataset='logs',
        sample_size=sample_size
    ))
    email_sample = list(query_job.result())
    
    # Process each email with each model
    model_results = {model: [] for model in comparison['models']}
    
    for email in email_sample:
        for model in comparison['models']:
            # Generate response with this model
            start_time = time.time()
            response = generate_response_with_model(
                model,
                email.from_email,
                email.subject,
                email.original_email
            )
            generation_time = time.time() - start_time
            
            # Store result
            model_results[model].append({
                'message_id': email.message_id,
                'response': response,
                'generation_time': generation_time,
                'token_count': count_tokens(response)
            })
    
    # Store results
    comparison['results'] = {
        'sample_size': len(email_sample),
        'completion_time': datetime.datetime.now().isoformat(),
        'model_results': model_results
    }
    
    db.collection('model_comparisons').document(comparison_id).set(comparison)
    
    return {'status': 'completed', 'sample_size': len(email_sample)}
```

3. **Results Analysis**

```python
def analyze_model_comparison(comparison_id):
    """Analyze results of a model comparison."""
    # Get comparison data
    db = firestore.Client()
    comparison = db.collection('model_comparisons').document(comparison_id).get().to_dict()
    
    if not comparison or 'results' not in comparison:
        return {'error': 'Comparison not found or incomplete'}
    
    # Calculate performance metrics for each model
    performance = {}
    for model, results in comparison['results']['model_results'].items():
        performance[model] = {
            'avg_generation_time': sum(r['generation_time'] for r in results) / len(results),
            'avg_token_count': sum(r['token_count'] for r in results) / len(results),
            'responses': len(results)
        }
    
    # If human evaluations are available, include them
    evaluations = db.collection('model_evaluations').where('comparison_id', '==', comparison_id).stream()
    
    evaluation_scores = {}
    for eval_doc in evaluations:
        eval_data = eval_doc.to_dict()
        model = eval_data['model']
        
        if model not in evaluation_scores:
            evaluation_scores[model] = {metric: [] for metric in comparison['metrics']}
        
        for metric in comparison['metrics']:
            if metric in eval_data:
                evaluation_scores[model][metric].append(eval_data[metric])
    
    # Calculate average scores
    for model, scores in evaluation_scores.items():
        if model in performance:
            performance[model]['human_evaluation'] = {
                metric: sum(values) / len(values) if values else 0
                for metric, values in scores.items()
            }
    
    return performance
```

## Continuous Improvement

### Feedback Loop Implementation

1. **Response Feedback Collection**

```python
def collect_response_feedback(message_id, feedback_type, feedback_text=None):
    """Collect feedback on AI responses."""
    # Store feedback
    db = firestore.Client()
    feedback = {
        'message_id': message_id,
        'feedback_type': feedback_type,
        'feedback_text': feedback_text,
        'timestamp': datetime.datetime.now()
    }
    
    db.collection('response_feedback').add(feedback)
    
    # Log feedback for analysis
    logging.info(f"Feedback received for message {message_id}: {feedback_type}")
    
    return {'status': 'recorded'}
```

2. **Feedback Analysis**

```python
def analyze_feedback_trends(days=30):
    """Analyze trends in response feedback."""
    # Get recent feedback
    db = firestore.Client()
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    
    feedback_query = db.collection('response_feedback').where(
        'timestamp', '>=', cutoff
    ).stream()
    
    # Categorize feedback
    feedback_types = {}
    feedback_by_day = {}
    
    for feedback in feedback_query:
        data = feedback.to_dict()
        
        # Count by type
        feedback_type = data['feedback_type']
        if feedback_type not in feedback_types:
            feedback_types[feedback_type] = 0
        feedback_types[feedback_type] += 1
        
        # Group by day
        day = data['timestamp'].date().isoformat()
        if day not in feedback_by_day:
            feedback_by_day[day] = {}
        
        if feedback_type not in feedback_by_day[day]:
            feedback_by_day[day][feedback_type] = 0
        feedback_by_day[day][feedback_type] += 1
    
    # Analyze text feedback
    text_feedback = []
    for feedback in feedback_query:
        data = feedback.to_dict()
        if data.get('feedback_text'):
            text_feedback.append(data['feedback_text'])
    
    # Perform simple text analysis if feedback exists
    common_terms = {}
    if text_feedback:
        from collections import Counter
        import re
        
        all_text = " ".join(text_feedback).lower()
        words = re.findall(r'\b\w+\b', all_text)
        common_terms = dict(Counter(words).most_common(20))
    
    return {
        'feedback_count': sum(feedback_types.values()),
        'by_type': feedback_types,
        'by_day': feedback_by_day,
        'common_terms': common_terms
    }
```

3. **Model Retraining Recommendations**

```python
def generate_improvement_recommendations():
    """Generate recommendations for model improvements based on feedback."""
    # Analyze recent feedback
    feedback_analysis = analyze_feedback_trends(days=30)
    
    # Get performance metrics
    performance_metrics = measure_response_times()
    error_rates = analyze_error_rates()
    
    # Generate recommendations
    recommendations = []
    
    # Check for high negative feedback
    negative_feedback = feedback_analysis['by_type'].get('negative', 0)
    total_feedback = feedback_analysis['feedback_count']
    
    if total_feedback > 0 and negative_feedback / total_feedback > 0.2:
        recommendations.append({
            'priority': 'high',
            'area': 'response_quality',
            'recommendation': 'Review prompt engineering due to high negative feedback rate',
            'data': f"{negative_feedback}/{total_feedback} responses received negative feedback"
        })
    
    # Check for slow response times
    if performance_metrics:
        recent_p95 = performance_metrics[0]['p95'] if performance_metrics else 0
        if recent_p95 > 10:  # More than 10 seconds for p95
            recommendations.append({
                'priority': 'high',
                'area': 'performance',
                'recommendation': 'Optimize response generation to improve speed',
                'data': f"P95 response time is {recent_p95:.2f} seconds"
            })
    
    # Check error rates
    if error_rates:
        latest_day = max(error_rates.keys())
        total_errors = sum(error_rates[latest_day].values())
        if total_errors > 10:
            recommendations.append({
                'priority': 'medium',
                'area': 'reliability',
                'recommendation': 'Address error patterns to improve reliability',
                'data': f"{total_errors} errors occurred on {latest_day}"
            })
    
    # Check common feedback terms
    if 'unclear' in feedback_analysis['common_terms'] or 'confusing' in feedback_analysis['common_terms']:
        recommendations.append({
            'priority': 'medium',
            'area': 'clarity',
            'recommendation': 'Improve response clarity based on feedback',
            'data': f"Common feedback terms include clarity issues"
        })
    
    return recommendations
```

### Implementation Checklist

Use this checklist to implement a comprehensive AI model evaluation system:

- [ ] **Setup Evaluation Infrastructure**
  - [ ] Configure logging for response metrics
  - [ ] Set up feedback collection mechanism
  - [ ] Create evaluation dashboards

- [ ] **Implement Regular Evaluations**
  - [ ] Weekly performance metric analysis
  - [ ] Monthly human evaluation of samples
  - [ ] Quarterly comprehensive model comparison

- [ ] **Establish Improvement Process**
  - [ ] Regular prompt engineering reviews
  - [ ] A/B testing of prompt variations
  - [ ] Feedback-driven model selection

- [ ] **Documentation and Reporting**
  - [ ] Create evaluation reports template
  - [ ] Document model performance history
  - [ ] Track improvement initiatives

## Conclusion

Effective AI model evaluation is critical for maintaining and improving the quality of your Auto Reply Email system. By implementing a structured evaluation framework that combines quantitative metrics with qualitative assessment, you can continuously refine your AI responses to better meet user needs and business objectives.

Remember that evaluation is an ongoing process. Regular assessment, combined with a robust feedback loop, will help ensure your system delivers consistently high-quality responses while adapting to changing requirements and user expectations.
