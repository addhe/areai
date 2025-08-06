# Panduan Rekayasa Prompt untuk Sistem Balas Email Otomatis

This guide provides best practices and techniques for optimizing AI prompts in the Auto Reply Email system to generate high-quality, contextual responses.

## Table of Contents

1. [Introduction to Prompt Engineering](#introduction-to-prompt-engineering)
2. [Prompt Structure](#prompt-structure)
3. [Tone and Style Guidelines](#tone-and-style-guidelines)
4. [Personalization Techniques](#personalization-techniques)
5. [Context Integration](#context-integration)
6. [Response Length Control](#response-length-control)
7. [Advanced Techniques](#advanced-techniques)
8. [Troubleshooting](#troubleshooting)
9. [Examples](#examples)

## Introduction to Prompt Engineering

Prompt engineering is the process of designing and refining input instructions to AI models to generate desired outputs. For the Auto Reply Email system, effective prompt engineering ensures:

- Professional and appropriate responses
- Contextual understanding of the original email
- Personalization based on customer data
- Consistent tone and style
- Efficient use of AI tokens

## Prompt Structure

The Auto Reply Email system uses a structured prompt format with the following components:

### 1. System Instructions

Define the AI's role and set general guidelines:

```
You are a professional email assistant for [Company Name]. 
Your task is to write a helpful, concise reply to the email below.
Always maintain a [tone] tone and be respectful of the sender's inquiry.
```

### 2. Context Information

Provide relevant information about the email and sender:

```
Email from: [sender_email]
Subject: [subject]
Customer status: [status]
Customer tier: [tier]
```

### 3. Original Email Content

Include the full or relevant portions of the original email:

```
--- Original Email ---
[email_body]
--- End Original Email ---
```

### 4. Response Instructions

Specific guidelines for generating the reply:

```
Write a reply that:
1. Acknowledges the sender's email
2. Addresses their specific questions or concerns
3. Provides relevant information or next steps
4. Ends with a professional closing
5. Includes a signature as [Your Company Name] Team
```

## Tone and Style Guidelines

The system supports different tones that can be customized based on your business needs:

### Formal Tone

```
Maintain a formal, professional tone. Use complete sentences and proper grammar.
Avoid contractions, slang, or overly casual language. Be respectful and precise.
```

### Friendly Tone

```
Use a warm, approachable tone while remaining professional. 
You may use some contractions and a conversational style.
Be personable but still maintain business etiquette.
```

### Technical Tone

```
Use precise technical language appropriate for the subject matter.
Be clear and specific with technical details while remaining accessible.
Focus on accuracy and completeness of information.
```

### Empathetic Tone

```
Show understanding and empathy for the sender's situation.
Acknowledge any concerns or frustrations they've expressed.
Use supportive language while maintaining professionalism.
```

## Personalization Techniques

Enhance responses with customer data for personalization:

### Basic Personalization

```
Address the customer by name: "Hello [customer_name],"
Reference their specific inquiry: "Regarding your question about [subject]..."
```

### Customer History Integration

```
"As a [tier] customer since [join_date]..."
"We see you recently purchased [product_name]..."
"Based on your previous interest in [category]..."
```

### Preference-Based Customization

```
"According to your communication preferences..."
"Based on your preferred [language/region/settings]..."
```

## Context Integration

Techniques to ensure the AI understands and responds to the specific context:

### Question Recognition

```
Identify all questions in the original email and ensure each one is addressed.
If a question is unclear, acknowledge this and provide the most helpful response possible.
```

### Topic Identification

```
Determine the main topic(s) of the email and focus the response accordingly.
If multiple topics are present, organize the response to address each one clearly.
```

### Sentiment Analysis

```
Recognize the sender's sentiment (positive, negative, neutral) and adjust the response tone accordingly.
For frustrated customers, acknowledge their concerns before providing solutions.
```

## Response Length Control

Guidelines for controlling the length of AI-generated responses:

### Concise Responses

```
Keep your response brief and to the point, ideally 3-5 sentences.
Focus only on the most relevant information needed to address the inquiry.
```

### Detailed Responses

```
Provide a comprehensive response that thoroughly addresses all points.
Include relevant details, explanations, and next steps as needed.
Organize longer responses with clear paragraphs or bullet points.
```

### Length Adaptation

```
Adjust the response length based on the complexity of the inquiry.
For simple questions, provide brief, direct answers.
For complex inquiries, provide more detailed explanations.
```

## Advanced Techniques

More sophisticated prompt engineering techniques:

### Few-Shot Learning

Include examples of ideal responses in the prompt:

```
Example 1:
Original: "When will my order arrive?"
Reply: "Thank you for your inquiry. Your order #12345 is scheduled for delivery on May 15th. You'll receive a tracking notification via email once it ships. Please let us know if you have any other questions."

Now respond to this email in a similar style:
```

### Chain-of-Thought

Guide the AI through a reasoning process:

```
First, identify the key questions or requests in the email.
Next, determine what information is needed to address each point.
Then, formulate a clear and concise response that addresses all points.
Finally, add an appropriate greeting and closing.
```

### Constraint Specification

Set specific constraints for the response:

```
Your response must:
- Be no longer than 150 words
- Not make promises about delivery dates
- Include a link to our FAQ page
- Avoid technical jargon
```

## Troubleshooting

Common issues and solutions:

### Issue: Generic Responses

**Solution:**
- Add more specific instructions about addressing the exact content
- Include more context about the customer and their inquiry
- Use few-shot examples of specific, helpful responses

### Issue: Incorrect Tone

**Solution:**
- Provide clearer tone guidelines with examples
- Add explicit instructions about formality level
- Include specific phrases to use or avoid

### Issue: Missing Information

**Solution:**
- Structure the prompt to require addressing specific points
- Use a checklist format for items that must be included
- Implement validation to check if all questions were answered

## Examples

### Example 1: Product Inquiry

**Prompt:**
```
You are a professional email assistant for Acme Tech. 
Your task is to write a helpful, concise reply to the email below.
Maintain a friendly yet professional tone.

Email from: john.doe@example.com
Subject: Product Compatibility Question
Customer status: Premium
Customer since: 2021

--- Original Email ---
Hello,

I recently purchased your XYZ-1000 router and I'm wondering if it's compatible with my ABC-200 modem. The modem is about 3 years old.

Also, do I need any special cables to connect them?

Thanks,
John
--- End Original Email ---

Write a reply that:
1. Addresses John by name
2. Answers both compatibility and cable questions
3. Acknowledges his premium customer status
4. Offers additional assistance
5. Ends with a professional closing
```

**Expected AI Response:**
```
Hello John,

Thank you for reaching out about your recent XYZ-1000 router purchase. As a valued premium customer, we're happy to help with your compatibility questions.

Good news! Your XYZ-1000 router is fully compatible with the ABC-200 modem. The router comes with a standard Ethernet cable that will work perfectly for connecting both devices. No special cables are needed for this setup.

For optimal performance, we recommend using the cable included with your new router, as it meets the specifications for maximum data transfer speeds between these devices.

If you need any assistance with setting up your network or have additional questions, please don't hesitate to contact us. As a premium customer, you also have access to our priority support line at 1-800-555-1234.

Best regards,
The Acme Tech Support Team
```

### Example 2: Technical Support

**Prompt:**
```
You are a technical support specialist for CloudServe Solutions.
Your task is to write a helpful, technical reply to the email below.
Maintain a professional tone while providing accurate technical information.

Email from: admin@company.example
Subject: API Connection Error
Customer status: Enterprise
Customer tier: Gold

--- Original Email ---
Hi Support,

We're getting consistent timeout errors when trying to connect to your REST API from our application. The error occurs about 60% of the time with error code 504.

We've checked our network and everything seems fine on our end. This started happening after your maintenance window yesterday.

Can you check if there are any issues on your side? This is affecting our production environment.

-Alex
--- End Original Email ---

Write a reply that:
1. Acknowledges the urgency of a production issue
2. Provides technical information about the 504 error
3. Explains any relevant findings from your side
4. Offers immediate next steps
5. Includes escalation options for an enterprise gold customer
```

**Expected AI Response:**
```
Hello Alex,

Thank you for reporting this issue with our REST API. We understand this is impacting your production environment and are treating it with high priority.

Our monitoring has confirmed intermittent 504 Gateway Timeout errors affecting approximately 15% of API requests following yesterday's maintenance window. This appears to be related to a load balancer configuration change that's causing connection pooling issues.

Our engineering team has:
1. Identified the root cause in the load balancer settings
2. Implemented a partial fix that has reduced error rates from 60% to approximately 15%
3. Scheduled a complete resolution within the next 2 hours

As a Gold tier Enterprise customer, we've already escalated this to our Senior Engineering team. Your dedicated Technical Account Manager, Sarah Johnson, has been notified and will be reaching out shortly with additional details.

In the meantime, you can implement retry logic with exponential backoff in your application as a temporary workaround. We recommend a maximum of 3 retries with a base delay of 1 second.

You can monitor our status page at status.cloudserve.example for real-time updates. For immediate assistance, please contact our Enterprise Support hotline at 1-888-555-4321 or reply directly to this email.

We apologize for the disruption and are working to fully resolve this as quickly as possible.

Best regards,
CloudServe Technical Support Team
```

### Example 3: Customer Service

**Prompt:**
```
You are a customer service representative for Green Grocery Delivery.
Your task is to write an empathetic, helpful reply to the email below.
Maintain a warm, understanding tone while resolving the customer's issue.

Email from: sarah.smith@example.com
Subject: Missing items in my delivery
Customer since: 2022-03-15
Recent orders: 5 orders in the last 30 days

--- Original Email ---
Hello,

I received my grocery delivery today (Order #GGD-29876), but several items were missing. I paid for organic apples, milk, and bread, but none of these were in my bags.

This is the second time this has happened this month. I'm really disappointed as I needed these items for dinner tonight.

Can I get a refund? And how can I make sure this doesn't happen again?

Sarah
--- End Original Email ---

Write a reply that:
1. Shows empathy for Sarah's situation
2. Addresses the immediate issue (missing items)
3. Offers a solution (refund process)
4. Explains how you'll prevent this in the future
5. Provides some form of goodwill gesture
```

**Expected AI Response:**
```
Hello Sarah,

I'm truly sorry to hear about the missing items in your delivery today. I understand how frustrating it must be to plan your meals only to find key ingredients missing, especially when this has happened before. This certainly doesn't meet the standard of service we aim to provide to our loyal customers.

I've processed a full refund for the missing organic apples, milk, and bread from order #GGD-29876. You'll see this credit returned to your original payment method within 1-2 business days.

I've also reviewed the notes on your account and can see this is indeed the second occurrence this month. I've flagged this to our fulfillment center manager, who will be implementing additional quality control checks specifically for your future orders. We're also conducting a broader review of our packing procedures to improve accuracy for all customers.

As a gesture of our appreciation for your patience and to make up for the inconvenience, I've added a $20 credit to your account and upgraded you to priority delivery status for your next three orders at no additional charge.

Would it be helpful if I arranged for the missing items to be delivered to you this evening? We could have them to you within the next 2 hours if that would help with your dinner plans.

Thank you for bringing this to our attention and giving us the opportunity to make things right. Your feedback helps us improve our service.

Warm regards,
Green Grocery Delivery Customer Care Team
```

## Conclusion

Effective prompt engineering is crucial for generating high-quality, contextual email responses. By following the guidelines and techniques in this document, you can optimize your Auto Reply Email system to provide professional, helpful, and personalized responses to customer inquiries.

Remember that prompt engineering is an iterative process. Regularly review AI-generated responses and refine your prompts based on performance and feedback. With continuous improvement, your system will become increasingly effective at handling a wide range of email communications.
