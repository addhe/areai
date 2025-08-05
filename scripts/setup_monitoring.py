#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Setup monitoring dashboard and alerts for Auto Reply Email system
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
        print("\033[1;36mChecking current GCP project...\033[0m")
        success, output = run_command("gcloud config get-value project", exit_on_error=False)
        
        if success and output and output.strip() != "(unset)":
            project_id = output.strip()
            print(f"\033[1;32mUsing current GCP project: {project_id}\033[0m")
        else:
            project_id = input("\033[1;33mEnter your GCP project ID: \033[0m")
            if not project_id:
                print("\033[1;31mProject ID is required. Exiting.\033[0m")
                sys.exit(1)
    
    return project_id


def create_notification_channel(project_id, channel_type, display_name, email=None):
    """Create a notification channel.
    
    Args:
        project_id (str): GCP project ID
        channel_type (str): Channel type (email, sms, etc.)
        display_name (str): Display name
        email (str): Email address for email channel
        
    Returns:
        str: Notification channel name or None if failed
    """
    print(f"\033[1;36mCreating notification channel: {display_name}\033[0m")
    
    # First check if a channel with this email already exists
    if channel_type == "email" and email:
        print(f"Checking for existing notification channels for {email}...")
        success, list_result = run_command(
            f"gcloud alpha monitoring channels list --project={project_id} --filter=\"labels.email_address='{email}'\"", 
            exit_on_error=False
        )
        
        if success and list_result and "name:" in list_result:
            # Extract channel name from output
            for line in list_result.splitlines():
                if line.startswith("name:"):
                    channel_name = line.split("name:")[1].strip()
                    print(f"\033[1;32mFound existing notification channel for {email}: {channel_name}\033[0m")
                    return channel_name
    
    # Create new channel
    cmd = [
        f"gcloud alpha monitoring channels create",
        f"--project={project_id}",
        f"--display-name='{display_name}'",
        f"--type={channel_type}"
    ]
    
    if channel_type == "email" and email:
        cmd.append(f"--channel-labels=email_address={email}")
    
    success, result = run_command(" ".join(cmd), exit_on_error=False)
    
    if not success:
        print(f"\033[1;31mFailed to create notification channel\033[0m")
        return None
        
    # Extract channel name from output
    for line in result.splitlines():
        if line.startswith("name:"):
            channel_name = line.split("name:")[1].strip()
            print(f"\033[1;32mCreated notification channel: {channel_name}\033[0m")
            return channel_name
    
    print("\033[1;31mCould not extract channel name from output\033[0m")
    return None


def generate_dashboard_template(output_file):
    """Generate a dashboard template JSON file.
    
    Args:
        output_file (str): Path to output file
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\033[1;36mGenerating dashboard template at {output_file}\033[0m")
    
    dashboard = {
        "displayName": "Auto Reply Email System Dashboard",
        "gridLayout": {
            "columns": 2,
            "widgets": [
                {
                    "title": "Email Processing Rate",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": "metric.type=\"cloudfunctions.googleapis.com/function/execution_count\" resource.type=\"cloud_function\" resource.label.\"function_name\"=\"auto-reply-email\"",
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_RATE"
                                        }
                                    },
                                    "unitOverride": "1"
                                },
                                "plotType": "LINE",
                                "targetAxis": "Y1"
                            }
                        ],
                        "timeshiftDuration": "0s",
                        "yAxis": {
                            "label": "y1Axis",
                            "scale": "LINEAR"
                        }
                    }
                },
                {
                    "title": "Response Generation Time",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": "metric.type=\"logging.googleapis.com/user/vertex_ai_response_time\" resource.type=\"cloud_function\" resource.label.\"function_name\"=\"auto-reply-email\"",
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_PERCENTILE_99"
                                        }
                                    },
                                    "unitOverride": "s"
                                },
                                "plotType": "LINE",
                                "targetAxis": "Y1"
                            }
                        ],
                        "timeshiftDuration": "0s",
                        "yAxis": {
                            "label": "y1Axis",
                            "scale": "LINEAR"
                        }
                    }
                },
                {
                    "title": "Function Execution Time",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": "metric.type=\"cloudfunctions.googleapis.com/function/execution_times\" resource.type=\"cloud_function\" resource.label.\"function_name\"=\"auto-reply-email\"",
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_PERCENTILE_95"
                                        }
                                    },
                                    "unitOverride": "ms"
                                },
                                "plotType": "LINE",
                                "targetAxis": "Y1"
                            }
                        ],
                        "timeshiftDuration": "0s",
                        "yAxis": {
                            "label": "y1Axis",
                            "scale": "LINEAR"
                        }
                    }
                },
                {
                    "title": "Error Count",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": "metric.type=\"logging.googleapis.com/log_entry_count\" resource.type=\"cloud_function\" resource.label.\"function_name\"=\"auto-reply-email\" severity>=\"ERROR\"",
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_COUNT"
                                        }
                                    },
                                    "unitOverride": "1"
                                },
                                "plotType": "LINE",
                                "targetAxis": "Y1"
                            }
                        ],
                        "timeshiftDuration": "0s",
                        "yAxis": {
                            "label": "y1Axis",
                            "scale": "LINEAR"
                        }
                    }
                }
            ]
        }
    }
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Write dashboard template
        with open(output_file, "w") as f:
            json.dump(dashboard, f, indent=2)
        
        print(f"\033[1;32mDashboard template generated at {output_file}\033[0m")
        return True
    except Exception as e:
        print(f"\033[1;31mFailed to generate dashboard template: {str(e)}\033[0m")
        return False


def deploy_dashboard(project_id, dashboard_file):
    """Deploy monitoring dashboard.
    
    Args:
        project_id (str): GCP project ID
        dashboard_file (str): Path to dashboard JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\033[1;36mDeploying dashboard from {dashboard_file}\033[0m")
    
    # Check if dashboard file exists
    if not os.path.exists(dashboard_file):
        print(f"\033[1;33mDashboard file {dashboard_file} not found\033[0m")
        
        # Ask user if they want to generate a template
        generate = input("Would you like to generate a dashboard template? (y/n): ").lower() == "y"
        if generate:
            if not generate_dashboard_template(dashboard_file):
                return False
        else:
            print("\033[1;31mDashboard deployment skipped\033[0m")
            return False
    
    try:
        # Read dashboard JSON
        with open(dashboard_file, "r") as f:
            dashboard_json = json.load(f)
        
        # Replace project ID placeholder if present
        dashboard_str = json.dumps(dashboard_json)
        if "${PROJECT_ID}" in dashboard_str:
            dashboard_str = dashboard_str.replace("${PROJECT_ID}", project_id)
            dashboard_json = json.loads(dashboard_str)
        
        # Write to temporary file
        temp_file = "/tmp/dashboard.json"
        with open(temp_file, "w") as f:
            json.dump(dashboard_json, f, indent=2)
        
        # Deploy dashboard
        cmd = f"gcloud monitoring dashboards create --project={project_id} --config-from-file={temp_file}"
        success, output = run_command(cmd, exit_on_error=False)
        
        if success:
            print("\033[1;32mDashboard deployed successfully\033[0m")
            
            # Extract dashboard URL if available
            for line in output.splitlines():
                if "https://" in line and "console.cloud.google.com" in line:
                    print(f"\033[1;36mDashboard URL: {line.strip()}\033[0m")
                    break
            return True
        else:
            print("\033[1;31mFailed to deploy dashboard\033[0m")
            return False
    except Exception as e:
        print(f"\033[1;31mError deploying dashboard: {str(e)}\033[0m")
        return False


def generate_alerts_template(output_file):
    """Generate an alerts template JSON file.
    
    Args:
        output_file (str): Path to output file
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\033[1;36mGenerating alerts template at {output_file}\033[0m")
    
    alerts = [
        {
            "displayName": "Auto Reply Email - High Error Rate",
            "conditions": [
                {
                    "displayName": "Error rate > 5%",
                    "conditionThreshold": {
                        "filter": "metric.type=\"cloudfunctions.googleapis.com/function/execution_count\" resource.type=\"cloud_function\" resource.label.\"function_name\"=\"auto-reply-email\" metric.label.\"status\"=\"error\"",
                        "aggregations": [
                            {
                                "alignmentPeriod": "60s",
                                "perSeriesAligner": "ALIGN_RATE"
                            }
                        ],
                        "comparison": "COMPARISON_GT",
                        "thresholdValue": 0.05,
                        "duration": "60s",
                        "trigger": {
                            "count": 1
                        }
                    }
                }
            ],
            "alertStrategy": {
                "autoClose": "300s"
            },
            "combiner": "OR",
            "enabled": True
        },
        {
            "displayName": "Auto Reply Email - Slow Response Time",
            "conditions": [
                {
                    "displayName": "Response time > 15s",
                    "conditionThreshold": {
                        "filter": "metric.type=\"logging.googleapis.com/user/vertex_ai_response_time\" resource.type=\"cloud_function\" resource.label.\"function_name\"=\"auto-reply-email\"",
                        "aggregations": [
                            {
                                "alignmentPeriod": "60s",
                                "perSeriesAligner": "ALIGN_PERCENTILE_95"
                            }
                        ],
                        "comparison": "COMPARISON_GT",
                        "thresholdValue": 15,
                        "duration": "300s",
                        "trigger": {
                            "count": 1
                        }
                    }
                }
            ],
            "alertStrategy": {
                "autoClose": "600s"
            },
            "combiner": "OR",
            "enabled": True
        },
        {
            "displayName": "Auto Reply Email - Function Execution Timeout",
            "conditions": [
                {
                    "displayName": "Function execution time > 30s",
                    "conditionThreshold": {
                        "filter": "metric.type=\"cloudfunctions.googleapis.com/function/execution_times\" resource.type=\"cloud_function\" resource.label.\"function_name\"=\"auto-reply-email\"",
                        "aggregations": [
                            {
                                "alignmentPeriod": "60s",
                                "perSeriesAligner": "ALIGN_PERCENTILE_95"
                            }
                        ],
                        "comparison": "COMPARISON_GT",
                        "thresholdValue": 30000,  # 30 seconds in ms
                        "duration": "300s",
                        "trigger": {
                            "count": 1
                        }
                    }
                }
            ],
            "alertStrategy": {
                "autoClose": "600s"
            },
            "combiner": "OR",
            "enabled": True
        }
    ]
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Write alerts template
        with open(output_file, "w") as f:
            json.dump(alerts, f, indent=2)
        
        print(f"\033[1;32mAlerts template generated at {output_file}\033[0m")
        return True
    except Exception as e:
        print(f"\033[1;31mFailed to generate alerts template: {str(e)}\033[0m")
        return False


def deploy_alerts(project_id, alerts_file, notification_channels=None):
    """Deploy alert policies.
    
    Args:
        project_id (str): GCP project ID
        alerts_file (str): Path to alerts JSON file
        notification_channels (list): List of notification channel names
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\033[1;36mDeploying alerts from {alerts_file}\033[0m")
    
    # Check if alerts file exists
    if not os.path.exists(alerts_file):
        print(f"\033[1;33mAlerts file {alerts_file} not found\033[0m")
        
        # Ask user if they want to generate a template
        generate = input("Would you like to generate an alerts template? (y/n): ").lower() == "y"
        if generate:
            if not generate_alerts_template(alerts_file):
                return False
        else:
            print("\033[1;31mAlerts deployment skipped\033[0m")
            return False
    
    try:
        # Read alerts JSON
        with open(alerts_file, "r") as f:
            alerts_json = json.load(f)
        
        # Add notification channels to each alert if provided
        if notification_channels:
            print(f"\033[1;36mAdding notification channels to alerts: {notification_channels}\033[0m")
            for alert in alerts_json:
                alert["notificationChannels"] = notification_channels
        
        # Deploy each alert policy
        success_count = 0
        for i, alert in enumerate(alerts_json):
            print(f"\033[1;36mDeploying alert policy '{alert['displayName']}'\033[0m")
            
            # Write to temporary file
            alert_file = f"/tmp/alert_{i}.json"
            with open(alert_file, "w") as f:
                json.dump(alert, f, indent=2)
            
            # Deploy alert policy
            cmd = f"gcloud alpha monitoring policies create --project={project_id} --policy-from-file={alert_file}"
            success, output = run_command(cmd, exit_on_error=False)
            
            if success:
                print(f"\033[1;32mAlert policy '{alert['displayName']}' deployed successfully\033[0m")
                success_count += 1
            else:
                print(f"\033[1;31mFailed to deploy alert policy '{alert['displayName']}'\033[0m")
        
        if success_count == len(alerts_json):
            print(f"\033[1;32mAll {success_count} alert policies deployed successfully\033[0m")
            return True
        elif success_count > 0:
            print(f"\033[1;33m{success_count} of {len(alerts_json)} alert policies deployed successfully\033[0m")
            return True
        else:
            print("\033[1;31mNo alert policies were deployed\033[0m")
            return False
    except Exception as e:
        print(f"\033[1;31mError deploying alerts: {str(e)}\033[0m")
        return False


def check_gcloud_installation():
    """Check if gcloud is installed.
    
    Returns:
        bool: True if gcloud is installed, False otherwise
    """
    print("\033[1;36mChecking if gcloud is installed...\033[0m")
    success, _ = run_command("which gcloud", exit_on_error=False)
    return success


def check_gcloud_auth():
    """Check if user is authenticated with gcloud.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    print("\033[1;36mChecking if user is authenticated with gcloud...\033[0m")
    success, output = run_command("gcloud auth list --filter=status:ACTIVE --format='value(account)'", exit_on_error=False)
    return success and output.strip() != ""


def check_monitoring_api_enabled(project_id):
    """Check if Cloud Monitoring API is enabled.
    
    Args:
        project_id (str): GCP project ID
        
    Returns:
        bool: True if enabled, False otherwise
    """
    print("\033[1;36mChecking if Cloud Monitoring API is enabled...\033[0m")
    success, output = run_command(
        f"gcloud services list --project={project_id} --filter=name:monitoring.googleapis.com --format='value(name)'",
        exit_on_error=False
    )
    return success and "monitoring.googleapis.com" in output


def enable_monitoring_api(project_id):
    """Enable Cloud Monitoring API.
    
    Args:
        project_id (str): GCP project ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    print("\033[1;36mEnabling Cloud Monitoring API...\033[0m")
    success, _ = run_command(
        f"gcloud services enable monitoring.googleapis.com --project={project_id}",
        exit_on_error=False
    )
    return success


def main():
    """Main function."""
    # Print banner
    print("\033[1;32m" + "=" * 80 + "\033[0m")
    print("\033[1;32m" + " " * 20 + "Auto Reply Email Monitoring Setup" + " " * 20 + "\033[0m")
    print("\033[1;32m" + "=" * 80 + "\033[0m\n")
    
    parser = argparse.ArgumentParser(description="Setup monitoring for Auto Reply Email system")
    parser.add_argument("--project-id", help="GCP project ID")
    parser.add_argument("--dashboard", default="../monitoring/dashboard.json", help="Path to dashboard JSON file")
    parser.add_argument("--alerts", default="../monitoring/alerts.json", help="Path to alerts JSON file")
    parser.add_argument("--email", help="Email address for notifications")
    parser.add_argument("--skip-dashboard", action="store_true", help="Skip dashboard deployment")
    parser.add_argument("--skip-alerts", action="store_true", help="Skip alerts deployment")
    parser.add_argument("--skip-checks", action="store_true", help="Skip prerequisite checks")
    parser.add_argument("--yes", "-y", action="store_true", help="Automatic yes to prompts")
    
    args = parser.parse_args()
    
    # Perform prerequisite checks
    if not args.skip_checks:
        # Check if gcloud is installed
        if not check_gcloud_installation():
            print("\033[1;31mError: gcloud is not installed. Please install the Google Cloud SDK.\033[0m")
            print("Visit https://cloud.google.com/sdk/docs/install for installation instructions.")
            sys.exit(1)
        
        # Check if user is authenticated
        if not check_gcloud_auth():
            print("\033[1;31mError: Not authenticated with gcloud. Please run 'gcloud auth login'.\033[0m")
            sys.exit(1)
    
    # Get project ID
    project_id = args.project_id or get_project_id()
    print(f"\033[1;36mUsing project ID: {project_id}\033[0m")
    
    # Check if Cloud Monitoring API is enabled
    if not args.skip_checks:
        if not check_monitoring_api_enabled(project_id):
            print("\033[1;33mCloud Monitoring API is not enabled.\033[0m")
            enable = args.yes or input("Would you like to enable it now? (y/n): ").lower() == "y"
            if enable:
                if enable_monitoring_api(project_id):
                    print("\033[1;32mCloud Monitoring API enabled successfully.\033[0m")
                else:
                    print("\033[1;31mFailed to enable Cloud Monitoring API. Please enable it manually.\033[0m")
                    sys.exit(1)
            else:
                print("\033[1;31mCloud Monitoring API is required. Exiting.\033[0m")
                sys.exit(1)
    
    # Resolve file paths
    script_dir = Path(__file__).parent.absolute()
    
    # Create monitoring directory if it doesn't exist
    monitoring_dir = script_dir.parent / "monitoring"
    os.makedirs(monitoring_dir, exist_ok=True)
    
    dashboard_file = Path(args.dashboard)
    if not dashboard_file.is_absolute():
        dashboard_file = script_dir / dashboard_file
    
    alerts_file = Path(args.alerts)
    if not alerts_file.is_absolute():
        alerts_file = script_dir / alerts_file
    
    # Create notification channel if email provided
    notification_channels = []
    if args.email:
        channel_name = create_notification_channel(
            project_id,
            "email",
            "Auto Reply Email Alerts",
            args.email
        )
        if channel_name:
            notification_channels.append(channel_name)
    elif not args.skip_alerts and not args.yes:
        # Prompt for email if not provided and not skipping alerts
        add_email = input("\033[1;33mNo email provided for notifications. Would you like to add one? (y/n): \033[0m").lower() == "y"
        if add_email:
            email = input("\033[1;36mEnter your email address: \033[0m")
            if email:
                channel_name = create_notification_channel(
                    project_id,
                    "email",
                    "Auto Reply Email Alerts",
                    email
                )
                if channel_name:
                    notification_channels.append(channel_name)
    
    # Track success of operations
    dashboard_success = True
    alerts_success = True
    
    # Deploy dashboard
    if not args.skip_dashboard:
        dashboard_success = deploy_dashboard(project_id, dashboard_file)
    else:
        print("\033[1;33mSkipping dashboard deployment\033[0m")
    
    # Deploy alerts
    if not args.skip_alerts:
        alerts_success = deploy_alerts(project_id, alerts_file, notification_channels)
    else:
        print("\033[1;33mSkipping alerts deployment\033[0m")
    
    # Print summary
    print("\n" + "\033[1;32m" + "=" * 80 + "\033[0m")
    print("\033[1;36mMonitoring Setup Summary:\033[0m")
    print("\033[1;32m" + "-" * 80 + "\033[0m")
    print(f"Project ID: {project_id}")
    
    if not args.skip_dashboard:
        status = "\033[1;32mSuccess\033[0m" if dashboard_success else "\033[1;31mFailed\033[0m"
        print(f"Dashboard Deployment: {status}")
    
    if not args.skip_alerts:
        status = "\033[1;32mSuccess\033[0m" if alerts_success else "\033[1;31mFailed\033[0m"
        print(f"Alerts Deployment: {status}")
    
    if notification_channels:
        print(f"Notification Channels: {len(notification_channels)} configured")
    else:
        print("Notification Channels: None configured")
    
    print("\033[1;32m" + "-" * 80 + "\033[0m")
    
    if dashboard_success and alerts_success:
        print("\033[1;32mMonitoring setup completed successfully!\033[0m")
        print("\033[1;36mYou can view your monitoring dashboard in the Google Cloud Console:\033[0m")
        print(f"https://console.cloud.google.com/monitoring/dashboards?project={project_id}")
    else:
        print("\033[1;31mMonitoring setup completed with some issues. Please check the logs above.\033[0m")
    
    print("\033[1;32m" + "=" * 80 + "\033[0m")


if __name__ == "__main__":
    main()
