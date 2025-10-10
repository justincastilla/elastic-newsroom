#!/usr/bin/env python3
"""
Elastic News - Detailed Workflow Test Runner

This script runs the detailed workflow test that shows real-time agent activity.
It's designed to demonstrate the complete multi-agent newsroom workflow.

Usage:
    python run_detailed_test.py
"""

import sys
import os
import subprocess
import time

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not available, try to load manually
    from pathlib import Path
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

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

def main():
    """Main entry point"""
    print("🏢 Elastic News - Detailed Workflow Test Runner")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('start_newsroom.sh'):
        print("❌ Please run this script from the elastic-news root directory")
        sys.exit(1)
    
    # Check if agents are running
    if not check_agents_running():
        print("\n🛑 Cannot run test - agents not ready")
        sys.exit(1)
    
    # Check if test file exists
    test_file = 'tests/test_newsroom_workflow_detailed.py'
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        sys.exit(1)
    
    print(f"\n🚀 Starting detailed workflow test...")
    print("   This will show real-time agent activity and timing")
    print("   Press Ctrl+C to stop the test")
    print("\n" + "=" * 60)
    
    # Run the test
    try:
        result = subprocess.run([sys.executable, test_file], check=True)
        print("\n✅ Test completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Test failed with exit code {e.returncode}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
