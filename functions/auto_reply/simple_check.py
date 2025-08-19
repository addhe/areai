#!/usr/bin/env python3
"""
Simple script to check Gmail auto-reply system components
"""

import subprocess
import sys

def run_command(cmd):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def main():
    print("🔍 Checking Gmail Auto-Reply System Components...")
    print("=" * 60)
    
    # Check Pub/Sub topics
    print("1. Checking Pub/Sub Topics...")
    success, stdout, stderr = run_command("gcloud pubsub topics list --project=awanmasterpiece")
    if success:
        if "gmail-notifications" in stdout:
            print("   ✅ gmail-notifications topic exists")
        else:
            print("   ❌ gmail-notifications topic not found")
            print("   📋 Available topics:")
            for line in stdout.strip().split('\n'):
                if line.strip():
                    print(f"      - {line.strip()}")
    else:
        print(f"   ❌ Error checking topics: {stderr}")
    
    # Check Pub/Sub subscriptions
    print("\n2. Checking Pub/Sub Subscriptions...")
    success, stdout, stderr = run_command("gcloud pubsub subscriptions list --project=awanmasterpiece")
    if success:
        if "gmail-notifications-sub" in stdout:
            print("   ✅ gmail-notifications-sub subscription exists")
        else:
            print("   ❌ gmail-notifications-sub subscription not found")
            print("   📋 Available subscriptions:")
            for line in stdout.strip().split('\n'):
                if line.strip():
                    print(f"      - {line.strip()}")
    else:
        print(f"   ❌ Error checking subscriptions: {stderr}")
    
    # Check Cloud Run service
    print("\n3. Checking Cloud Run Service...")
    success, stdout, stderr = run_command("gcloud run services describe auto-reply-email --region=us-central1 --project=awanmasterpiece --format='value(status.url)'")
    if success and stdout.strip():
        print(f"   ✅ Cloud Run service is running: {stdout.strip()}")
    else:
        print(f"   ❌ Error checking Cloud Run service: {stderr}")
    
    # Check if service is healthy
    print("\n4. Checking Service Health...")
    success, stdout, stderr = run_command("curl -s https://auto-reply-email-361046956504.us-central1.run.app/ | grep -q 'healthy'")
    if success:
        print("   ✅ Service is healthy")
    else:
        print("   ❌ Service health check failed")
    
    print("\n" + "=" * 60)
    print("📝 Next Steps:")
    print("   If Pub/Sub components are missing, run:")
    print("   python setup_gmail_watch.py")
    print("\n   To test the system, send an email to:")
    print("   squidgamecs2025@gmail.com")

if __name__ == "__main__":
    main()
