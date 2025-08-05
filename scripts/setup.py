#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Setup script for the Auto Reply Email system

This script helps set up the necessary dependencies and configuration for the
Auto Reply Email system. It performs the following tasks:
1. Checks and installs required Python packages
2. Verifies Google Cloud SDK installation
3. Guides through project setup and API enablement
4. Helps set up initial configuration

Usage:
    python setup.py [--install-deps] [--check-only] [--verbose]
"""

import argparse
import os
import platform
import subprocess
import sys
from typing import List, Dict, Tuple, Optional


# Constants
REQUIRED_PACKAGES = [
    "google-api-python-client",
    "google-auth-httplib2",
    "google-auth-oauthlib",
    "google-cloud-pubsub",
    "google-cloud-functions",
    "google-cloud-logging",
    "google-cloud-secretmanager",
    "google-cloud-aiplatform",
    "requests",
    "python-dateutil"
]

REQUIRED_APIS = [
    "gmail.googleapis.com",
    "pubsub.googleapis.com",
    "cloudfunctions.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "logging.googleapis.com"
]

CONFIG_TEMPLATE = """
# Auto Reply Email System Configuration

# Google Cloud Project Settings
PROJECT_ID={project_id}
REGION={region}

# Gmail API Settings
GMAIL_PUBSUB_TOPIC={pubsub_topic}
GMAIL_OAUTH_SECRET={oauth_secret}

# Cloud Function Settings
FUNCTION_NAME={function_name}
FUNCTION_TIMEOUT={function_timeout}
FUNCTION_MEMORY={function_memory}

# Vertex AI Settings
VERTEX_AI_MODEL={vertex_ai_model}
RESPONSE_TIMEOUT={response_timeout}

# Customer API Settings
CUSTOMER_API_ENDPOINT={customer_api_endpoint}
CUSTOMER_API_KEY={customer_api_key}

# Logging Settings
LOG_LEVEL={log_level}

# Feature Flags
ENABLE_MOCK_CUSTOMER_API={enable_mock_customer_api}
ENABLE_FALLBACK_RESPONSES={enable_fallback_responses}
"""


def print_step(step: str) -> None:
    """Print a setup step with formatting.
    
    Args:
        step: Step description
    """
    print(f"\n\033[1;34m=== {step} ===\033[0m")


def print_success(message: str) -> None:
    """Print a success message with formatting.
    
    Args:
        message: Success message
    """
    print(f"\033[1;32m✓ {message}\033[0m")


def print_error(message: str) -> None:
    """Print an error message with formatting.
    
    Args:
        message: Error message
    """
    print(f"\033[1;31m✗ {message}\033[0m")


def print_warning(message: str) -> None:
    """Print a warning message with formatting.
    
    Args:
        message: Warning message
    """
    print(f"\033[1;33m! {message}\033[0m")


def print_info(message: str) -> None:
    """Print an info message with formatting.
    
    Args:
        message: Info message
    """
    print(f"\033[1;36m> {message}\033[0m")


def check_python_version() -> bool:
    """Check if Python version is 3.7 or higher.
    
    Returns:
        bool: True if Python version is compatible, False otherwise
    """
    major, minor, _ = platform.python_version_tuple()
    version_ok = int(major) >= 3 and int(minor) >= 7
    
    if version_ok:
        print_success(f"Python version {platform.python_version()} is compatible")
    else:
        print_error(f"Python version {platform.python_version()} is not compatible (3.7+ required)")
    
    return version_ok


def check_installed_packages() -> Tuple[List[str], List[str]]:
    """Check which required packages are installed.
    
    Returns:
        Tuple[List[str], List[str]]: Lists of installed and missing packages
    """
    installed = []
    missing = []
    
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package.replace("-", "_").split(">=")[0])
            installed.append(package)
        except ImportError:
            missing.append(package)
    
    return installed, missing


def install_packages(packages: List[str], verbose: bool = False) -> bool:
    """Install missing packages using pip.
    
    Args:
        packages: List of packages to install
        verbose: Whether to show detailed output
        
    Returns:
        bool: True if installation succeeded, False otherwise
    """
    if not packages:
        return True
    
    print_info(f"Installing {len(packages)} missing packages...")
    
    cmd = [sys.executable, "-m", "pip", "install"] + packages
    
    try:
        if verbose:
            subprocess.run(cmd, check=True)
        else:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print_success("Package installation completed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install packages: {e}")
        return False


def check_gcloud_sdk() -> bool:
    """Check if Google Cloud SDK is installed.
    
    Returns:
        bool: True if gcloud is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["gcloud", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            version_line = result.stdout.splitlines()[0]
            print_success(f"Google Cloud SDK is installed: {version_line}")
            return True
        else:
            print_error("Google Cloud SDK is not installed or not in PATH")
            return False
    except FileNotFoundError:
        print_error("Google Cloud SDK is not installed or not in PATH")
        return False


def check_gcloud_auth() -> bool:
    """Check if user is authenticated with gcloud.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    try:
        result = subprocess.run(
            ["gcloud", "auth", "list"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0 and "No credentialed accounts." not in result.stdout:
            account = None
            for line in result.stdout.splitlines():
                if "*" in line:
                    account = line.split()[1]
                    break
            
            if account:
                print_success(f"Authenticated with Google Cloud as: {account}")
                return True
            else:
                print_error("Not authenticated with Google Cloud")
                return False
        else:
            print_error("Not authenticated with Google Cloud")
            return False
    except subprocess.CalledProcessError:
        print_error("Failed to check Google Cloud authentication")
        return False


def get_current_project() -> Optional[str]:
    """Get the current Google Cloud project.
    
    Returns:
        Optional[str]: Project ID if set, None otherwise
    """
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip() and result.stdout.strip() != "(unset)":
            return result.stdout.strip()
        else:
            return None
    except subprocess.CalledProcessError:
        return None


def check_api_enabled(project_id: str, api: str) -> bool:
    """Check if a specific API is enabled for the project.
    
    Args:
        project_id: Google Cloud project ID
        api: API identifier
        
    Returns:
        bool: True if API is enabled, False otherwise
    """
    try:
        result = subprocess.run(
            ["gcloud", "services", "list", "--project", project_id, "--filter", f"config.name:{api}"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        return result.returncode == 0 and api in result.stdout
    except subprocess.CalledProcessError:
        return False


def enable_api(project_id: str, api: str, verbose: bool = False) -> bool:
    """Enable a specific API for the project.
    
    Args:
        project_id: Google Cloud project ID
        api: API identifier
        verbose: Whether to show detailed output
        
    Returns:
        bool: True if API was enabled successfully, False otherwise
    """
    try:
        cmd = ["gcloud", "services", "enable", api, "--project", project_id]
        
        if verbose:
            subprocess.run(cmd, check=True)
        else:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return True
    except subprocess.CalledProcessError:
        return False


def create_config_file(config_path: str, config_values: Dict[str, str]) -> bool:
    """Create a configuration file with the provided values.
    
    Args:
        config_path: Path to the configuration file
        config_values: Dictionary of configuration values
        
    Returns:
        bool: True if file was created successfully, False otherwise
    """
    try:
        with open(config_path, 'w') as f:
            f.write(CONFIG_TEMPLATE.format(**config_values))
        
        print_success(f"Created configuration file: {config_path}")
        return True
    except Exception as e:
        print_error(f"Failed to create configuration file: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Setup script for Auto Reply Email system')
    parser.add_argument('--install-deps', action='store_true', help='Install missing dependencies')
    parser.add_argument('--check-only', action='store_true', help='Only check requirements without setup')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    
    args = parser.parse_args()
    
    print("\n🔧 Auto Reply Email System Setup")
    print("===============================")
    
    # Step 1: Check Python version
    print_step("Checking Python version")
    python_ok = check_python_version()
    if not python_ok:
        print_warning("Please upgrade to Python 3.7 or higher")
    
    # Step 2: Check required packages
    print_step("Checking required packages")
    installed_packages, missing_packages = check_installed_packages()
    
    if installed_packages:
        print_success(f"Found {len(installed_packages)} installed packages")
        if args.verbose:
            for pkg in installed_packages:
                print(f"  - {pkg}")
    
    if missing_packages:
        print_warning(f"Missing {len(missing_packages)} required packages")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        
        if args.install_deps:
            install_packages(missing_packages, args.verbose)
        else:
            print_info("Run with --install-deps to install missing packages")
    else:
        print_success("All required packages are installed")
    
    if args.check_only:
        sys.exit(0 if python_ok and not missing_packages else 1)
    
    # Step 3: Check Google Cloud SDK
    print_step("Checking Google Cloud SDK")
    gcloud_ok = check_gcloud_sdk()
    
    if not gcloud_ok:
        print_info("Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    
    # Step 4: Check Google Cloud authentication
    print_step("Checking Google Cloud authentication")
    auth_ok = check_gcloud_auth()
    
    if not auth_ok:
        print_info("Please authenticate with Google Cloud:")
        print("  gcloud auth login")
        sys.exit(1)
    
    # Step 5: Check current project
    print_step("Checking Google Cloud project")
    current_project = get_current_project()
    
    if current_project:
        print_success(f"Current project: {current_project}")
        use_current = input("Use this project for Auto Reply Email system? (y/n): ").lower() == 'y'
        
        if not use_current:
            current_project = input("Enter Google Cloud project ID: ")
    else:
        print_warning("No Google Cloud project is currently set")
        current_project = input("Enter Google Cloud project ID: ")
    
    # Step 6: Check required APIs
    print_step("Checking required APIs")
    apis_to_enable = []
    
    for api in REQUIRED_APIS:
        if check_api_enabled(current_project, api):
            print_success(f"API enabled: {api}")
        else:
            print_warning(f"API not enabled: {api}")
            apis_to_enable.append(api)
    
    if apis_to_enable:
        enable_apis = input("Enable required APIs? (y/n): ").lower() == 'y'
        
        if enable_apis:
            for api in apis_to_enable:
                print_info(f"Enabling API: {api}")
                if enable_api(current_project, api, args.verbose):
                    print_success(f"Enabled API: {api}")
                else:
                    print_error(f"Failed to enable API: {api}")
    
    # Step 7: Create configuration
    print_step("Creating configuration")
    
    config_values = {
        "project_id": current_project,
        "region": input("Enter GCP region (default: us-central1): ") or "us-central1",
        "pubsub_topic": input("Enter Pub/Sub topic name (default: gmail-notifications): ") or "gmail-notifications",
        "oauth_secret": input("Enter OAuth secret name (default: gmail-oauth-token): ") or "gmail-oauth-token",
        "function_name": input("Enter Cloud Function name (default: process-email): ") or "process-email",
        "function_timeout": input("Enter Cloud Function timeout in seconds (default: 60): ") or "60",
        "function_memory": input("Enter Cloud Function memory in MB (default: 256): ") or "256",
        "vertex_ai_model": input("Enter Vertex AI model name (default: gemini-1.0-pro): ") or "gemini-1.0-pro",
        "response_timeout": input("Enter response timeout in seconds (default: 15): ") or "15",
        "customer_api_endpoint": input("Enter Customer API endpoint (default: https://example.com/api/v1/customers): ") or "https://example.com/api/v1/customers",
        "customer_api_key": input("Enter Customer API key (leave blank for none): ") or "",
        "log_level": input("Enter log level (default: INFO): ") or "INFO",
        "enable_mock_customer_api": input("Enable mock Customer API for testing? (true/false, default: true): ") or "true",
        "enable_fallback_responses": input("Enable fallback responses? (true/false, default: true): ") or "true"
    }
    
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.env")
    create_config_file(config_path, config_values)
    
    # Step 8: Next steps
    print_step("Setup completed")
    print_info("Next steps:")
    print("  1. Run gmail_auth.py to set up Gmail API authentication")
    print("  2. Deploy the Cloud Function using deploy.py")
    print("  3. Test the system using test_email.py")


if __name__ == '__main__':
    main()
