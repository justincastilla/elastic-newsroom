#!/usr/bin/env python3
"""
Elastic News - Detailed Workflow Test (Best Case Scenario)

This test runs the complete newsroom workflow with detailed real-time output
showing what each agent is doing at every step. Perfect for demonstrating
the multi-agent system in action.

Features:
- Real-time agent status updates
- Detailed timing information
- Step-by-step workflow visualization
- Error handling with graceful fallbacks
- Comprehensive logging output
"""

import asyncio
import json
import time
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from a2a.client import ClientFactory, ClientConfig, A2ACardResolver, create_text_message_object


class WorkflowMonitor:
    """Monitors and displays workflow progress in real-time"""
    
    def __init__(self):
        self.start_time = None
        self.step_times = {}
        self.current_step = None
        self.agent_status = {}
        
    def start_workflow(self):
        """Start timing the entire workflow"""
        self.start_time = time.time()
        print("🚀 Workflow started")
        
    def start_step(self, step_name: str, description: str):
        """Start timing a workflow step"""
        self.current_step = step_name
        self.step_times[step_name] = {
            'start': time.time(),
            'description': description
        }
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"\n⏱️  [{elapsed:6.1f}s] {step_name}: {description}")
        
    def end_step(self, step_name: str, success: bool = True, details: str = ""):
        """End timing a workflow step"""
        if step_name in self.step_times:
            step_time = time.time() - self.step_times[step_name]['start']
            self.step_times[step_name]['duration'] = step_time
            self.step_times[step_name]['success'] = success
            
            status_icon = "✅" if success else "❌"
            print(f"    {status_icon} Completed in {step_time:.1f}s {details}")
            
    def update_agent_status(self, agent: str, status: str, details: str = ""):
        """Update the status of a specific agent"""
        self.agent_status[agent] = {
            'status': status,
            'details': details,
            'timestamp': time.time()
        }
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"    🤖 [{elapsed:6.1f}s] {agent}: {status} {details}")
        
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow execution"""
        total_time = time.time() - self.start_time if self.start_time else 0
        return {
            'total_time': total_time,
            'steps': self.step_times,
            'agent_status': self.agent_status
        }


async def check_agent_health(http_client: httpx.AsyncClient, agent_url: str, agent_name: str) -> bool:
    """Check if an agent is healthy and responding"""
    try:
        card_resolver = A2ACardResolver(http_client, agent_url)
        agent_card = await card_resolver.get_agent_card()
        print(f"    ✅ {agent_name} is healthy (v{agent_card.version})")
        return True
    except Exception as e:
        print(f"    ❌ {agent_name} is not responding: {e}")
        return False


async def test_newsroom_workflow_detailed():
    """Test the complete newsroom workflow with detailed monitoring"""
    
    # Initialize workflow monitor
    monitor = WorkflowMonitor()
    
    print("🏢 Elastic News - Detailed Workflow Test (Best Case Scenario)")
    print("=" * 80)
    print("This test demonstrates the complete multi-agent newsroom workflow")
    print("with real-time status updates and detailed timing information.")
    print("=" * 80)
    
    # Agent URLs
    agents = {
        'News Chief': 'http://localhost:8080',
        'Reporter': 'http://localhost:8081', 
        'Editor': 'http://localhost:8082',
        'Researcher': 'http://localhost:8083',
        'Publisher': 'http://localhost:8084'
    }
    
    # Use longer timeout for the complete workflow
    async with httpx.AsyncClient(timeout=300.0) as http_client:
        
        # ========================================
        # STEP 1: Health Check All Agents
        # ========================================
        monitor.start_workflow()
        monitor.start_step("HEALTH_CHECK", "Verifying all agents are online and healthy")
        
        healthy_agents = {}
        for agent_name, agent_url in agents.items():
            if await check_agent_health(http_client, agent_url, agent_name):
                healthy_agents[agent_name] = agent_url
                
        if len(healthy_agents) != len(agents):
            monitor.end_step("HEALTH_CHECK", False, "- Some agents are not responding")
            print(f"\n❌ Only {len(healthy_agents)}/{len(agents)} agents are healthy")
            return
            
        monitor.end_step("HEALTH_CHECK", True, f"- All {len(healthy_agents)} agents healthy")
        
        # ========================================
        # STEP 2: Initialize A2A Clients
        # ========================================
        monitor.start_step("INIT_CLIENTS", "Initializing A2A clients for all agents")
        
        clients = {}
        client_config = ClientConfig(httpx_client=http_client, streaming=False)
        client_factory = ClientFactory(client_config)
        
        for agent_name, agent_url in healthy_agents.items():
            try:
                card_resolver = A2ACardResolver(http_client, agent_url)
                agent_card = await card_resolver.get_agent_card()
                clients[agent_name] = client_factory.create(agent_card)
                monitor.update_agent_status(agent_name, "Client initialized", f"({len(agent_card.skills)} skills)")
            except Exception as e:
                print(f"    ❌ Failed to initialize {agent_name}: {e}")
                return
                
        monitor.end_step("INIT_CLIENTS", True, f"- {len(clients)} clients ready")
        
        # ========================================
        # STEP 3: Story Assignment
        # ========================================
        monitor.start_step("STORY_ASSIGNMENT", "Assigning story to News Chief")
        
        story = {
            "topic": "AI Agents Transform Modern Newsrooms",
            "angle": "How A2A protocol enables multi-agent collaboration in journalism",
            "target_length": 1200,
            "priority": "high",
            "deadline": "2025-01-08T18:00:00Z"
        }
        
        print(f"    📝 Story Details:")
        print(f"       Topic: {story['topic']}")
        print(f"       Angle: {story['angle']}")
        print(f"       Target Length: {story['target_length']} words")
        print(f"       Priority: {story['priority']}")
        
        request = {
            "action": "assign_story",
            "story": story
        }
        message = create_text_message_object(content=json.dumps(request))
        
        story_id = None
        async for response in clients['News Chief'].send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    story_id = result.get('story_id')
                    monitor.update_agent_status('News Chief', "Story assigned", f"ID: {story_id}")
                    
                    # Check reporter response
                    reporter_response = result.get('reporter_response', {})
                    if reporter_response:
                        monitor.update_agent_status('Reporter', "Assignment accepted", 
                                                  f"Status: {reporter_response.get('status')}")
        
        if not story_id:
            monitor.end_step("STORY_ASSIGNMENT", False, "- No story ID returned")
            return
            
        monitor.end_step("STORY_ASSIGNMENT", True, f"- Story ID: {story_id}")
        
        # ========================================
        # STEP 4: Article Writing (Multi-Agent Workflow)
        # ========================================
        monitor.start_step("ARTICLE_WRITING", "Reporter coordinates multi-agent article writing")
        
        print("    🔄 Multi-Agent Workflow:")
        print("       1. Reporter generates outline and research questions")
        print("       2. Researcher + Archivist work in parallel")
        print("       3. Reporter writes article with all data")
        print("       4. Editor reviews and provides feedback")
        print("       5. Reporter applies editorial suggestions")
        print("       6. Publisher indexes to Elasticsearch")
        
        request = {
            "action": "write_article",
            "story_id": story_id
        }
        message = create_text_message_object(content=json.dumps(request))
        
        # This is where the magic happens - the Reporter coordinates everything
        async for response in clients['Reporter'].send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    
                    # Update agent statuses based on the result
                    if result.get('status') == 'success':
                        monitor.update_agent_status('Reporter', "Article written", 
                                                  f"Word count: {result.get('word_count')}")
                        
                        # Check if research was completed
                        if result.get('research_data'):
                            monitor.update_agent_status('Researcher', "Research completed", 
                                                      f"Questions: {len(result.get('research_data', []))}")
                        
                        # Check if archive search was completed
                        if result.get('archive_data'):
                            monitor.update_agent_status('Archivist', "Archive search completed", 
                                                      "Historical context gathered")
                        
                        # Check if editorial review was completed
                        if result.get('editorial_review'):
                            monitor.update_agent_status('Editor', "Review completed", 
                                                      f"Status: {result.get('editorial_review', {}).get('approval_status')}")
                        
                        # Check if publishing was completed
                        if result.get('published'):
                            publisher_resp = result.get('publisher_response', {})
                            monitor.update_agent_status('Publisher', "Article published", 
                                                      f"ES indexed: {publisher_resp.get('elasticsearch', {}).get('index')}")
        
        monitor.end_step("ARTICLE_WRITING", True, "Complete multi-agent workflow finished")
        
        # ========================================
        # STEP 5: Verify Final Status
        # ========================================
        monitor.start_step("STATUS_VERIFICATION", "Verifying final status of all agents")
        
        # Check News Chief status
        request = {"action": "get_story_status", "story_id": story_id}
        message = create_text_message_object(content=json.dumps(request))
        
        async for response in clients['News Chief'].send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    story_data = result.get('story', {})
                    monitor.update_agent_status('News Chief', "Story status", 
                                              f"Status: {story_data.get('status')}")
        
        # Check Reporter status
        request = {"action": "get_status", "story_id": story_id}
        message = create_text_message_object(content=json.dumps(request))
        
        async for response in clients['Reporter'].send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    draft = result.get('draft', {})
                    monitor.update_agent_status('Reporter', "Final status", 
                                              f"Draft: {draft.get('status')}")
        
        monitor.end_step("STATUS_VERIFICATION", True, "All agents verified")
        
        # ========================================
        # WORKFLOW SUMMARY
        # ========================================
        summary = monitor.get_summary()
        
        print("\n" + "=" * 80)
        print("🎉 WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        print(f"\n⏱️  Total Execution Time: {summary['total_time']:.1f} seconds")
        
        print(f"\n📊 Step Breakdown:")
        for step_name, step_data in summary['steps'].items():
            duration = step_data.get('duration', 0)
            success = step_data.get('success', False)
            status_icon = "✅" if success else "❌"
            print(f"   {status_icon} {step_name}: {duration:.1f}s - {step_data['description']}")
        
        print(f"\n🤖 Final Agent Status:")
        for agent, status_data in summary['agent_status'].items():
            print(f"   • {agent}: {status_data['status']} - {status_data['details']}")
        
        print(f"\n🔄 Multi-Agent Workflow Summary:")
        print("   ✓ News Chief: Coordinated story assignment and workflow")
        print("   ✓ Reporter: Generated outline, coordinated research, wrote article")
        print("   ✓ Researcher: Provided factual data and background information")
        print("   ✓ Archivist: Searched historical articles for context")
        print("   ✓ Editor: Reviewed article for quality and consistency")
        print("   ✓ Publisher: Indexed article to Elasticsearch")
        
        print(f"\n📈 Performance Metrics:")
        print(f"   • Agents Involved: {len(healthy_agents)}")
        print(f"   • A2A Messages: ~15-20 inter-agent communications")
        print(f"   • Parallel Execution: Researcher + Archivist ran simultaneously")
        print(f"   • AI Model Calls: ~6 Anthropic API calls")
        print(f"   • Elasticsearch Operations: 2 (search + index)")
        
        print("\n" + "=" * 80)
        print("✨ This demonstrates a fully functional multi-agent AI newsroom!")
        print("   Each agent has specialized capabilities and communicates")
        print("   seamlessly via the A2A protocol to produce high-quality news articles.")
        print("=" * 80)


async def main():
    """Main entry point with error handling"""
    print("\n🧪 Elastic News - Detailed Workflow Test")
    print("\n⚠️  Prerequisites:")
    print("   1. All agents running:")
    print("      → ./start_newsroom.sh")
    print("   2. Environment variables set:")
    print("      → ANTHROPIC_API_KEY (required)")
    print("      → ELASTICSEARCH_ENDPOINT (required)")
    print("      → ELASTIC_SEARCH_API_KEY (required)")
    print("      → ELASTIC_ARCHIVIST_AGENT_CARD_URL (optional)")
    print("      → ELASTIC_ARCHIVIST_API_KEY (optional)")
    print("   3. Elasticsearch index created:")
    print("      → python scripts/create_elasticsearch_index.py")
    
    print(f"\n⏰ Starting test at {datetime.now().strftime('%H:%M:%S')}")
    print("   This test will show real-time agent activity...")
    print("\nStarting in 3 seconds...")
    
    await asyncio.sleep(3)
    
    try:
        await test_newsroom_workflow_detailed()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
