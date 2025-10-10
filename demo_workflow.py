#!/usr/bin/env python3
"""
Elastic News - Workflow Demonstration Script

This script provides an easy way to demonstrate the multi-agent newsroom workflow.
It includes setup verification, agent health checks, and runs the detailed test.

Usage:
    python demo_workflow.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not available, try to load manually
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"🏢 {title}")
    print("=" * 80)

def print_step(step_num, title, description=""):
    """Print a formatted step"""
    print(f"\n📋 STEP {step_num}: {title}")
    if description:
        print(f"   {description}")
    print("-" * 60)

def check_file_exists(filepath, description):
    """Check if a file exists and print status"""
    if os.path.exists(filepath):
        print(f"   ✅ {description}: {filepath}")
        return True
    else:
        print(f"   ❌ {description}: {filepath} (NOT FOUND)")
        return False

def check_env_var(var_name, description):
    """Check if an environment variable is set"""
    value = os.getenv(var_name)
    if value:
        # Mask sensitive values
        masked_value = value[:8] + "..." if len(value) > 8 else value
        print(f"   ✅ {description}: {masked_value}")
        return True
    else:
        print(f"   ❌ {description}: Not set")
        return False

def run_command(cmd, description, check=True):
    """Run a command and return success status"""
    print(f"   🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {description} completed successfully")
            return True
        else:
            print(f"   ❌ {description} failed (exit code: {result.returncode})")
            if result.stderr:
                print(f"      Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"   ❌ {description} failed: {e}")
        return False

def main():
    """Main demonstration script"""
    print_header("Elastic News - Multi-Agent Workflow Demonstration")
    
    print("This script will demonstrate the complete multi-agent newsroom workflow")
    print("with real-time monitoring and detailed output.")
    
    # Check if we're in the right directory
    if not os.path.exists('start_newsroom.sh'):
        print("\n❌ Please run this script from the elastic-news root directory")
        print("   Current directory:", os.getcwd())
        sys.exit(1)
    
    print_step(1, "Environment Verification", "Checking required files and environment variables")
    
    # Check required files
    files_ok = True
    files_ok &= check_file_exists('start_newsroom.sh', 'Start script')
    files_ok &= check_file_exists('tests/test_newsroom_workflow_detailed.py', 'Detailed test')
    files_ok &= check_file_exists('run_detailed_test.py', 'Test runner')
    files_ok &= check_file_exists('scripts/create_elasticsearch_index.py', 'ES index script')
    
    # Check environment variables
    env_ok = True
    env_ok &= check_env_var('ANTHROPIC_API_KEY', 'Anthropic API Key')
    env_ok &= check_env_var('ELASTICSEARCH_ENDPOINT', 'Elasticsearch Endpoint')
    env_ok &= check_env_var('ELASTIC_SEARCH_API_KEY', 'Elasticsearch API Key')
    
    # Optional environment variables
    archivist_ok = check_env_var('ELASTIC_ARCHIVIST_AGENT_CARD_URL', 'Archivist Agent URL (optional)')
    archivist_key_ok = check_env_var('ELASTIC_ARCHIVIST_API_KEY', 'Archivist API Key (optional)')
    
    if not files_ok:
        print("\n❌ Missing required files. Please ensure you're in the correct directory.")
        sys.exit(1)
    
    if not env_ok:
        print("\n❌ Missing required environment variables.")
        print("   Please create a .env file with the required credentials.")
        print("   See env.example for reference.")
        sys.exit(1)
    
    if not archivist_ok or not archivist_key_ok:
        print("\n⚠️  Archivist credentials not set - historical search will be skipped")
        print("   This is optional but recommended for the full experience.")
    
    print_step(2, "Agent Health Check", "Verifying all agents are running")
    
    # Check if agents are running
    agents_running = run_command(
        "python run_detailed_test.py --check-only",
        "Checking agent health",
        check=False
    )
    
    if not agents_running:
        print("\n🔄 Starting agents...")
        start_success = run_command(
            "./start_newsroom.sh",
            "Starting all agents"
        )
        
        if not start_success:
            print("\n❌ Failed to start agents. Please check the logs.")
            sys.exit(1)
        
        print("\n⏳ Waiting for agents to initialize...")
        time.sleep(5)
        
        # Check again
        agents_running = run_command(
            "python run_detailed_test.py --check-only",
            "Re-checking agent health",
            check=False
        )
        
        if not agents_running:
            print("\n❌ Agents still not responding. Please check the logs:")
            print("   tail -f logs/*.log")
            sys.exit(1)
    
    print_step(3, "Elasticsearch Index Check", "Ensuring Elasticsearch index exists")
    
    # Check if Elasticsearch index exists
    index_ok = run_command(
        "python scripts/create_elasticsearch_index.py",
        "Creating/verifying Elasticsearch index",
        check=False
    )
    
    if not index_ok:
        print("\n⚠️  Elasticsearch index creation failed, but continuing...")
        print("   The test may still work with limited functionality.")
    
    print_step(4, "Workflow Demonstration", "Running the detailed workflow test")
    
    print("\n🚀 Starting the multi-agent workflow demonstration...")
    print("   This will show real-time agent activity and timing.")
    print("   Press Ctrl+C to stop the demonstration.")
    
    # Run the detailed test
    test_success = run_command(
        "python tests/test_newsroom_workflow_detailed.py",
        "Running detailed workflow test",
        check=False
    )
    
    if test_success:
        print_header("Demonstration Completed Successfully!")
        print("\n✨ The multi-agent newsroom workflow has been demonstrated.")
        print("   All agents worked together to produce a complete news article.")
        print("\n📊 What you just saw:")
        print("   • 5 specialized AI agents collaborating via A2A protocol")
        print("   • Real-time coordination and status updates")
        print("   • Parallel processing for efficiency")
        print("   • Complete article generation and publication")
        print("   • Elasticsearch integration for search and indexing")
        
        print("\n🔍 To explore further:")
        print("   • View generated articles: ls -la articles/")
        print("   • Check agent logs: tail -f logs/*.log")
        print("   • Run the test again: python run_detailed_test.py")
        print("   • Start the web UI: ./start_newsroom.sh --with-ui")
        
    else:
        print_header("Demonstration Completed with Issues")
        print("\n⚠️  The workflow completed but encountered some issues.")
        print("   Check the logs above for details.")
        print("\n🔍 To troubleshoot:")
        print("   • Check agent logs: tail -f logs/*.log")
        print("   • Verify environment variables: cat .env")
        print("   • Restart agents: ./start_newsroom.sh --stop && ./start_newsroom.sh")
    
    print("\n" + "=" * 80)
    print("🎉 Thank you for exploring Elastic News!")
    print("   This demonstrates the power of multi-agent AI systems")
    print("   working together to produce high-quality content.")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demonstration interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
