#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Deployment script for Auto Reply Email system
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, capture_output=True, exit_on_error=True):
    """Run a shell command.
    
    Args:
        cmd (str): Command to run
        capture_output (bool): Whether to capture output
        exit_on_error (bool): Whether to exit on error
        
    Returns:
        tuple: (success, output) where success is a boolean and output is the command output
    """
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"\033[1;31mError executing command: {cmd}\033[0m")
            print(f"\033[1;31mError: {result.stderr}\033[0m")
            if exit_on_error:
                sys.exit(1)
            return False, result.stderr if capture_output else None
            
        return True, result.stdout if capture_output else None
    except Exception as e:
        print(f"\033[1;31mException executing command: {cmd}\033[0m")
        print(f"\033[1;31mError: {str(e)}\033[0m")
        if exit_on_error:
            sys.exit(1)
        return False, str(e)


def get_project_id():
    """Get GCP project ID.
    
    Returns:
        str: GCP project ID
    """
    project_id = os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        try:
            project_id = run_command("gcloud config get-value project").strip()
        except Exception:
            project_id = input("Enter your GCP project ID: ")
    
    return project_id


def enable_apis(project_id):
    """Enable required GCP APIs.
    
    Args:
        project_id (str): GCP project ID
    """
    print("Enabling required APIs...")
    apis = [
        "gmail.googleapis.com",
        "pubsub.googleapis.com",
        "cloudfunctions.googleapis.com",
        "aiplatform.googleapis.com",
        "secretmanager.googleapis.com"
    ]
    
    cmd = f"gcloud services enable {' '.join(apis)} --project={project_id}"
    run_command(cmd, capture_output=False)
    
    print("APIs enabled successfully")


def create_service_account(project_id, sa_name="autoreply-sa"):
    """Create service account for Auto Reply Email.
    
    Args:
        project_id (str): GCP project ID
        sa_name (str): Service account name
        
    Returns:
        str: Service account email
    """
    print(f"Creating service account: {sa_name}")
    
    # Check if service account already exists
    try:
        cmd = f"gcloud iam service-accounts describe {sa_name}@{project_id}.iam.gserviceaccount.com --project={project_id}"
        run_command(cmd)
        print(f"Service account {sa_name} already exists")
    except Exception:
        # Create service account
        cmd = f"gcloud iam service-accounts create {sa_name} \
            --description=\"Service Account for Auto Reply Email with AI\" \
            --display-name=\"Auto Reply Email SA\" \
            --project={project_id}"
        run_command(cmd, capture_output=False)
    
    # Grant required roles
    roles = [
        "roles/pubsub.subscriber",
        "roles/aiplatform.user",
        "roles/gmail.modify",
        "roles/secretmanager.secretAccessor"
    ]
    
    for role in roles:
        cmd = f"gcloud projects add-iam-policy-binding {project_id} \
            --member=\"serviceAccount:{sa_name}@{project_id}.iam.gserviceaccount.com\" \
            --role=\"{role}\""
        run_command(cmd, capture_output=False)
    
    print("Service account created and roles assigned")
    return f"{sa_name}@{project_id}.iam.gserviceaccount.com"


def setup_pubsub(project_id, topic_name="new-email"):
    """Set up Pub/Sub topic and subscription.
    
    Args:
        project_id (str): GCP project ID
        topic_name (str): Pub/Sub topic name
    """
    print(f"Setting up Pub/Sub topic: {topic_name}")
    
    # Create topic
    try:
        cmd = f"gcloud pubsub topics create {topic_name} --project={project_id}"
        run_command(cmd, capture_output=False)
    except Exception:
        print(f"Topic {topic_name} already exists")
    
    # Create subscription
    try:
        cmd = f"gcloud pubsub subscriptions create email-subscriber --topic={topic_name} --project={project_id}"
        run_command(cmd, capture_output=False)
    except Exception:
        print("Subscription email-subscriber already exists")
    
    print("Pub/Sub setup completed")


def setup_secrets(project_id):
    """Set up Secret Manager secrets.
    
    Args:
        project_id (str): GCP project ID
    """
    print("Setting up Secret Manager secrets")
    
    secrets = [
        "gmail-oauth-token",
        "customer-api-key"
    ]
    
    for secret in secrets:
        try:
            cmd = f"gcloud secrets create {secret} --replication-policy=\"automatic\" --project={project_id}"
            run_command(cmd, capture_output=False)
        except Exception:
            print(f"Secret {secret} already exists")
    
    print("Secret Manager setup completed")


def deploy_cloud_function(project_id, region, sa_email, function_path):
    """Deploy Cloud Function.
    
    Args:
        project_id (str): GCP project ID
        region (str): GCP region
        sa_email (str): Service account email
        function_path (str): Path to function code
    """
    print("Deploying Cloud Function...")
    
    cmd = f"gcloud functions deploy auto-reply-email \
        --runtime python311 \
        --trigger-topic new-email \
        --entry-point pubsub_trigger \
        --service-account {sa_email} \
        --region {region} \
        --memory 256MB \
        --timeout 60s \
        --source {function_path} \
        --set-env-vars GCP_PROJECT_ID={project_id},GCP_REGION={region} \
        --project={project_id}"
    
    run_command(cmd, capture_output=False)
    
    print("Cloud Function deployed successfully")


def setup_oauth(script_path):
    """Set up OAuth for Gmail API.
    
    Args:
        script_path (str): Path to Gmail auth script
    """
    print("Setting up OAuth for Gmail API")
    
    cmd = f"python {script_path}"
    run_command(cmd, capture_output=False)
    
    print("OAuth setup completed")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Deploy Auto Reply Email system")
    parser.add_argument("--project-id", help="GCP project ID")
    parser.add_argument("--region", default="us-central1", help="GCP region")
    parser.add_argument("--skip-apis", action="store_true", help="Skip enabling APIs")
    parser.add_argument("--skip-sa", action="store_true", help="Skip service account creation")
    parser.add_argument("--skip-pubsub", action="store_true", help="Skip Pub/Sub setup")
    parser.add_argument("--skip-secrets", action="store_true", help="Skip Secret Manager setup")
    parser.add_argument("--skip-function", action="store_true", help="Skip Cloud Function deployment")
    parser.add_argument("--skip-oauth", action="store_true", help="Skip OAuth setup")
    
    args = parser.parse_args()
    
    # Get project ID
    project_id = args.project_id or get_project_id()
    print(f"Using project ID: {project_id}")
    
    # Resolve paths
    script_dir = Path(__file__).parent.absolute()
    project_dir = script_dir.parent
    function_path = project_dir / "cloud_function"
    gmail_auth_script = script_dir / "gmail_auth.py"
    
    # Enable APIs
    if not args.skip_apis:
        enable_apis(project_id)
    
    # Create service account
    sa_email = None
    if not args.skip_sa:
        sa_email = create_service_account(project_id)
    else:
        sa_email = f"autoreply-sa@{project_id}.iam.gserviceaccount.com"
    
    # Set up Pub/Sub
    if not args.skip_pubsub:
        setup_pubsub(project_id)
    
    # Set up Secret Manager
    if not args.skip_secrets:
        setup_secrets(project_id)
    
    # Set up OAuth
    if not args.skip_oauth:
        setup_oauth(gmail_auth_script)
    
    # Deploy Cloud Function
    if not args.skip_function:
        deploy_cloud_function(project_id, args.region, sa_email, function_path)
    
    print("\nDeployment completed successfully!")
    print("\nNext steps:")
    print("1. Upload OAuth token to Secret Manager:")
    print(f"   gcloud secrets versions add gmail-oauth-token --data-file=token.json --project={project_id}")
    print("2. Set up Gmail API watch:")
    print(f"   python {script_dir}/gmail_auth.py --setup-watch")
    print("3. Set up monitoring:")
    print(f"   python {script_dir}/setup_monitoring.py --email=your-email@example.com")
    print("4. Test the system:")
    print(f"   python {script_dir}/test_email.py --to=your-email@example.com")


if __name__ == "__main__":
    main()
