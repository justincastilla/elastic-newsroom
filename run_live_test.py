#!/usr/bin/env python3
"""
Elastic News - Live Workflow Test Runner

This script provides easy access to different levels of live workflow testing
with real-time monitoring and detailed output.

Usage:
    python run_live_test.py [basic|live|advanced]
"""

import sys
import os
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

def check_agents_running():
    """Check if all required agents are running"""
    agents = {
        'News Chief': 'http://localhost:8080',
        'Reporter': 'http://localhost:8081',
        'Editor': 'http://localhost:8082', 
        'Researcher': 'http://localhost:8083',
        'Publisher': 'http://localhost:8084'
    }
    
    print("🔍 Checking if all agents are running...")
    
    import httpx
    import asyncio
    from a2a.client import A2ACardResolver
    
    async def check_agent(agent_name, agent_url):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                card_resolver = A2ACardResolver(client, agent_url)
                await card_resolver.get_agent_card()
                return True
        except:
            return False
    
    async def check_all_agents():
        results = []
        for agent_name, agent_url in agents.items():
            is_running = await check_agent(agent_name, agent_url)
            results.append((agent_name, is_running))
            status = "✅" if is_running else "❌"
            print(f"   {status} {agent_name}: {agent_url}")
        return results
    
    results = asyncio.run(check_all_agents())
    running_agents = [name for name, running in results if running]
    
    if len(running_agents) != len(agents):
        print(f"\n❌ Only {len(running_agents)}/{len(agents)} agents are running")
        print("\n💡 To start all agents, run:")
        print("   ./start_newsroom.sh")
        return False
    
    print(f"\n✅ All {len(agents)} agents are running and healthy!")
    return True

def run_test(test_type):
    """Run the specified test type"""
    
    test_files = {
        'basic': 'tests/test_newsroom_workflow_detailed.py',
        'live': 'tests/test_newsroom_workflow_live.py',
        'advanced': 'tests/test_newsroom_workflow_advanced.py',
        'comprehensive': 'tests/test_newsroom_workflow_comprehensive.py'
    }
    
    test_descriptions = {
        'basic': 'Basic detailed test with step-by-step monitoring',
        'live': 'Live test with real-time Reporter status updates',
        'advanced': 'Advanced test with granular multi-agent monitoring',
        'comprehensive': 'Comprehensive test monitoring ALL agents in real-time'
    }
    
    if test_type not in test_files:
        print(f"❌ Unknown test type: {test_type}")
        print("Available types: basic, live, advanced, comprehensive")
        return False
    
    test_file = test_files[test_type]
    description = test_descriptions[test_type]
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"\n🚀 Running {test_type.upper()} test: {description}")
    print(f"   Test file: {test_file}")
    print("   Press Ctrl+C to stop the test")
    print("\n" + "=" * 80)
    
    try:
        result = subprocess.run([sys.executable, test_file], check=True)
        print("\n✅ Test completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Test failed with exit code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        return False

def main():
    """Main entry point"""
    print_header("Elastic News - Live Workflow Test Runner")
    
    # Check if we're in the right directory
    if not os.path.exists('start_newsroom.sh'):
        print("❌ Please run this script from the elastic-news root directory")
        sys.exit(1)
    
    # Get test type from command line or prompt user
    test_type = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not test_type:
        print("Available test types:")
        print("   basic         - Basic detailed test with step-by-step monitoring")
        print("   live          - Live test with real-time Reporter status updates")
        print("   advanced      - Advanced test with granular multi-agent monitoring")
        print("   comprehensive - Comprehensive test monitoring ALL agents in real-time")
        print()
        test_type = input("Enter test type (basic/live/advanced/comprehensive): ").strip().lower()
    
    if test_type not in ['basic', 'live', 'advanced', 'comprehensive']:
        print("❌ Invalid test type. Please choose: basic, live, advanced, or comprehensive")
        sys.exit(1)
    
    print_step(1, "Environment Verification", "Checking required files and environment variables")
    
    # Check required files
    files_ok = True
    files_ok &= os.path.exists('start_newsroom.sh')
    files_ok &= os.path.exists(f'tests/test_newsroom_workflow_{test_type}.py')
    
    if not files_ok:
        print("❌ Missing required files. Please ensure you're in the correct directory.")
        sys.exit(1)
    
    # Check environment variables
    env_ok = True
    env_ok &= os.getenv('ANTHROPIC_API_KEY') is not None
    env_ok &= os.getenv('ELASTICSEARCH_ENDPOINT') is not None
    env_ok &= os.getenv('ELASTIC_SEARCH_API_KEY') is not None
    
    if not env_ok:
        print("❌ Missing required environment variables.")
        print("   Please create a .env file with the required credentials.")
        print("   See env.example for reference.")
        sys.exit(1)
    
    print_step(2, "Agent Health Check", "Verifying all agents are running")
    
    # Check if agents are running
    if not check_agents_running():
        print("\n🔄 Starting agents...")
        start_success = subprocess.run(["./start_newsroom.sh"], check=True)
        
        if start_success.returncode != 0:
            print("❌ Failed to start agents. Please check the logs.")
            sys.exit(1)
        
        print("\n⏳ Waiting for agents to initialize...")
        time.sleep(5)
        
        # Check again
        if not check_agents_running():
            print("❌ Agents still not responding. Please check the logs:")
            print("   tail -f logs/*.log")
            sys.exit(1)
    
    print_step(3, f"{test_type.upper()} Workflow Test", f"Running {test_type} live workflow test")
    
    # Run the test
    test_success = run_test(test_type)
    
    if test_success:
        print_header("Test Completed Successfully!")
        print("\n✨ The multi-agent newsroom workflow has been demonstrated.")
        print("   All agents worked together to produce a complete news article.")
        
        print(f"\n📊 What you just saw ({test_type} test):")
        if test_type == 'basic':
            print("   • Step-by-step workflow monitoring")
            print("   • Detailed timing information")
            print("   • Agent status tracking")
        elif test_type == 'live':
            print("   • Real-time Reporter status updates")
            print("   • Live workflow progress tracking")
            print("   • Enhanced monitoring of coordination")
        elif test_type == 'advanced':
            print("   • Granular multi-agent monitoring")
            print("   • Real-time status from all agents")
            print("   • Parallel task execution tracking")
        
        print("\n🔍 To explore further:")
        print("   • View generated articles: ls -la articles/")
        print("   • Check agent logs: tail -f logs/*.log")
        print("   • Run different test levels: python run_live_test.py [basic|live|advanced]")
        print("   • Start the web UI: ./start_newsroom.sh --with-ui")
        
    else:
        print_header("Test Completed with Issues")
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
        print("\n\n⏹️  Test runner interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
