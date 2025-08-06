#!/usr/bin/env python3
"""
Script to setup permissions for Gmail API watch
"""

import subprocess
import sys

def run_command(cmd):
    """Run a command and return the result."""
    try:
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"✅ Success: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Setup permissions for Gmail API watch."""
    print("🔐 Setting up Gmail API Watch Permissions...")
    print("=" * 60)
    
    PROJECT_ID = "awanmasterpiece"
    TOPIC_NAME = "gmail-notifications"
    
    # Add Gmail service account permission to publish to our topic
    print("1. Adding Gmail API service account permission to Pub/Sub topic...")
    cmd = f"gcloud pubsub topics add-iam-policy-binding {TOPIC_NAME} --member=serviceAccount:gmail-api-push@system.gserviceaccount.com --role=roles/pubsub.publisher --project={PROJECT_ID}"
    success1 = run_command(cmd)
    
    # Also add our service account permission to the topic (just in case)
    print("\n2. Adding our service account permission to Pub/Sub topic...")
    cmd = f"gcloud pubsub topics add-iam-policy-binding {TOPIC_NAME} --member=serviceAccount:autoreply-sa@{PROJECT_ID}.iam.gserviceaccount.com --role=roles/pubsub.publisher --project={PROJECT_ID}"
    success2 = run_command(cmd)
    
    # Check topic permissions
    print("\n3. Checking topic permissions...")
    cmd = f"gcloud pubsub topics get-iam-policy {TOPIC_NAME} --project={PROJECT_ID}"
    success3 = run_command(cmd)
    
    print("\n" + "=" * 60)
    if success1:
        print("✅ Gmail API service account permission added successfully!")
        print("📝 Now you can try running: python setup_gmail_watch.py")
    else:
        print("❌ Failed to add Gmail API service account permission")
        print("💡 You may need to run this manually:")
        print(f"   gcloud pubsub topics add-iam-policy-binding {TOPIC_NAME} \\")
        print(f"   --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \\")
        print(f"   --role=roles/pubsub.publisher --project={PROJECT_ID}")

if __name__ == "__main__":
    main()
