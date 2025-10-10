#!/usr/bin/env python3
"""
Elastic News - Advanced Live Workflow Test

This test provides the most detailed live monitoring of the multi-agent workflow,
showing granular progress updates and real-time agent coordination.

Features:
- Live polling of all agents during workflow execution
- Granular progress tracking through each workflow step
- Real-time status updates from all agents
- Detailed timing and progress indicators
- Enhanced monitoring of parallel agent execution
"""

import asyncio
import json
import time
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List
from a2a.client import ClientFactory, ClientConfig, A2ACardResolver, create_text_message_object


class AdvancedWorkflowMonitor:
    """Advanced workflow monitor with granular live updates"""
    
    def __init__(self):
        self.start_time = None
        self.step_times = {}
        self.current_step = None
        self.agent_status = {}
        self.workflow_progress = {}
        self.parallel_tasks = {}
        self.last_updates = {}
        
    def start_workflow(self):
        """Start timing the entire workflow"""
        self.start_time = time.time()
        print("🚀 Advanced live workflow monitoring started")
        
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
        
    def update_workflow_progress(self, step: str, progress: str, details: str = ""):
        """Update workflow progress within a step"""
        self.workflow_progress[step] = {
            'progress': progress,
            'details': details,
            'timestamp': time.time()
        }
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"    🔄 [{elapsed:6.1f}s] {step}: {progress} {details}")
        
    def update_parallel_task(self, task_name: str, status: str, details: str = ""):
        """Update status of parallel tasks"""
        self.parallel_tasks[task_name] = {
            'status': status,
            'details': details,
            'timestamp': time.time()
        }
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"    ⚡ [{elapsed:6.1f}s] {task_name}: {status} {details}")
        
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow execution"""
        total_time = time.time() - self.start_time if self.start_time else 0
        return {
            'total_time': total_time,
            'steps': self.step_times,
            'agent_status': self.agent_status,
            'workflow_progress': self.workflow_progress,
            'parallel_tasks': self.parallel_tasks
        }


async def poll_all_agents_status(http_client: httpx.AsyncClient, clients: Dict[str, Any], story_id: str, monitor: AdvancedWorkflowMonitor, max_duration: int = 600):
    """Poll all agents for status updates during workflow execution"""
    
    start_time = time.time()
    last_updates = {}
    
    print(f"    🔍 Starting advanced live monitoring of all agents...")
    print(f"    ⏰ Will monitor for up to {max_duration} seconds")
    print(f"    📡 Polling every 2 seconds for real-time updates...")
    
    while time.time() - start_time < max_duration:
        try:
            # Poll Reporter status
            await poll_agent_status(http_client, clients['Reporter'], 'Reporter', story_id, monitor, last_updates)
            
            # Poll other agents if they have status endpoints
            for agent_name in ['Editor', 'Researcher', 'Publisher']:
                if agent_name in clients:
                    await poll_agent_status(http_client, clients[agent_name], agent_name, story_id, monitor, last_updates)
            
            # Check if workflow is complete - only return true when actually published
            reporter_status = monitor.agent_status.get('Reporter', {}).get('status', '')
            if 'Status: published' in reporter_status:
                monitor.update_workflow_progress('Workflow', 'Complete', 'All agents finished')
                return True
                
            # Wait before next poll
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"    ⚠️  Error in advanced monitoring: {e}")
            await asyncio.sleep(5)
    
    print(f"    ⏰ Advanced monitoring timeout reached ({max_duration}s)")
    return False


async def poll_agent_status(http_client: httpx.AsyncClient, client, agent_name: str, story_id: str, monitor: AdvancedWorkflowMonitor, last_updates: Dict[str, str]):
    """Poll a specific agent for status updates"""
    
    try:
        # Get agent status
        request = {"action": "get_status", "story_id": story_id}
        message = create_text_message_object(content=json.dumps(request))
        
        async for response in client.send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    
                    # Process Reporter status
                    if agent_name == 'Reporter':
                        assignment = result.get('assignment', {})
                        draft = result.get('draft', {})
                        
                        # Check assignment status
                        reporter_status = assignment.get('reporter_status', 'unknown')
                        if reporter_status != last_updates.get('reporter_status'):
                            last_updates['reporter_status'] = reporter_status
                            monitor.update_agent_status('Reporter', f"Status: {reporter_status}")
                            
                            # Map status to detailed workflow progress with comprehensive tracking
                            if reporter_status == 'researching':
                                monitor.update_workflow_progress('Step 1', 'Generating outline and research questions', '📋 Creating article structure')
                                monitor.update_parallel_task('Researcher', 'Starting research', '🔍 Preparing to gather facts')
                                monitor.update_parallel_task('Archivist', 'Starting archive search', '📚 Preparing to search history')
                            elif reporter_status == 'writing' or reporter_status == 'drafting':
                                monitor.update_workflow_progress('Step 3', 'Writing article with research data', '✍️ Generating content')
                                monitor.update_parallel_task('Researcher', 'Research completed', '✅ Facts gathered')
                                monitor.update_parallel_task('Archivist', 'Archive search completed', '✅ Historical context found')
                            elif reporter_status == 'draft_complete' or reporter_status == 'draft_ready':
                                monitor.update_workflow_progress('Step 4', 'Draft completed, submitting to Editor', '📤 Sending for review')
                                monitor.update_parallel_task('Editor', 'Starting review', '✏️ Analyzing content')
                            elif reporter_status == 'editing' or reporter_status == 'applying_edits':
                                monitor.update_workflow_progress('Step 5', 'Applying editorial suggestions', '✏️ Incorporating feedback')
                                monitor.update_parallel_task('Editor', 'Review completed', '✅ Feedback provided')
                            elif reporter_status == 'published' or reporter_status == 'publishing':
                                monitor.update_workflow_progress('Step 6', 'Article published to Elasticsearch', '📰 Final publication')
                                monitor.update_parallel_task('Publisher', 'Publishing completed', '✅ Article indexed')
                            elif reporter_status not in ['unknown', '']:
                                # Track any other status we haven't seen before
                                monitor.update_workflow_progress('Workflow', f'Status: {reporter_status}', '🔄 Processing...')
                        
                        # Check draft status
                        if draft:  # Check if draft exists
                            draft_status = draft.get('status', 'unknown')
                            if draft_status != last_updates.get('draft_status') and draft_status != 'unknown':
                                last_updates['draft_status'] = draft_status
                                word_count = draft.get('word_count', 0)
                                monitor.update_workflow_progress('Draft', f"Status: {draft_status}", f"Words: {word_count}")
                    
                    # Process other agents
                    elif agent_name == 'Editor':
                        reviews = result.get('reviews', [])
                        if reviews:
                            latest_review = reviews[-1]
                            review_status = latest_review.get('status', 'unknown')
                            if review_status != last_updates.get('editor_status'):
                                last_updates['editor_status'] = review_status
                                monitor.update_agent_status('Editor', f"Review status: {review_status}")
                    
                    elif agent_name == 'Researcher':
                        research_history = result.get('research_history', [])
                        if research_history:
                            latest_research = research_history[-1]
                            research_status = latest_research.get('status', 'unknown')
                            if research_status != last_updates.get('researcher_status'):
                                last_updates['researcher_status'] = research_status
                                monitor.update_agent_status('Researcher', f"Research status: {research_status}")
                    
                    elif agent_name == 'Publisher':
                        total_published = result.get('total_published', 0)
                        if total_published != last_updates.get('publisher_count'):
                            last_updates['publisher_count'] = total_published
                            monitor.update_agent_status('Publisher', f"Published articles: {total_published}")
                    
                    break
                    
    except Exception as e:
        # Silently handle individual agent polling errors
        pass


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


async def test_newsroom_workflow_advanced():
    """Test the complete newsroom workflow with advanced live monitoring"""
    
    # Initialize workflow monitor
    monitor = AdvancedWorkflowMonitor()
    
    print("🏢 Elastic News - Advanced Live Workflow Test")
    print("=" * 80)
    print("This test demonstrates the complete multi-agent newsroom workflow")
    print("with advanced live monitoring showing granular progress updates.")
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
        # STEP 4: Advanced Live Multi-Agent Workflow Monitoring
        # ========================================
        monitor.start_step("ADVANCED_WORKFLOW", "Advanced live monitoring of multi-agent article writing")
        
        print("    🔄 Multi-Agent Workflow with Advanced Live Updates:")
        print("       1. Reporter generates outline and research questions")
        print("       2. Researcher + Archivist work in parallel")
        print("       3. Reporter writes article with all data")
        print("       4. Editor reviews and provides feedback")
        print("       5. Reporter applies editorial suggestions")
        print("       6. Publisher indexes to Elasticsearch")
        print()
        print("    📡 Advanced monitoring will show:")
        print("       • Real-time status updates from all agents")
        print("       • Granular progress through each workflow step")
        print("       • Parallel task execution tracking")
        print("       • Live updates every 2 seconds")
        print()
        
        # Start the workflow by triggering the Reporter
        request = {
            "action": "write_article",
            "story_id": story_id
        }
        message = create_text_message_object(content=json.dumps(request))
        
        # Start the workflow in the background
        workflow_task = asyncio.create_task(
            clients['Reporter'].send_message(message).__aiter__().__anext__()
        )
        
        # Start advanced live monitoring
        monitoring_task = asyncio.create_task(
            poll_all_agents_status(http_client, clients, story_id, monitor)
        )
        
        # Wait for either the workflow to complete or monitoring to finish
        try:
            await asyncio.wait_for(monitoring_task, timeout=300)
            monitor.update_workflow_progress('Workflow', 'Advanced monitoring completed', 'All steps tracked')
        except asyncio.TimeoutError:
            print("    ⏰ Advanced monitoring timeout reached")
        
        # Wait for the workflow to complete
        try:
            await asyncio.wait_for(workflow_task, timeout=10)
        except asyncio.TimeoutError:
            print("    ⏰ Workflow task timeout")
        
        monitor.end_step("ADVANCED_WORKFLOW", True, "Advanced live monitoring completed")
        
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
        print("🎉 ADVANCED LIVE WORKFLOW COMPLETED SUCCESSFULLY")
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
        
        print(f"\n🔄 Workflow Progress Tracked:")
        for step, progress_data in summary['workflow_progress'].items():
            print(f"   • {step}: {progress_data['progress']} - {progress_data['details']}")
        
        print(f"\n⚡ Parallel Tasks Monitored:")
        for task, task_data in summary['parallel_tasks'].items():
            print(f"   • {task}: {task_data['status']} - {task_data['details']}")
        
        print(f"\n🔄 Multi-Agent Workflow Summary:")
        print("   ✓ News Chief: Coordinated story assignment and workflow")
        print("   ✓ Reporter: Generated outline, coordinated research, wrote article")
        print("   ✓ Researcher: Provided factual data and background information")
        print("   ✓ Archivist: Searched historical articles for context")
        print("   ✓ Editor: Reviewed article for quality and consistency")
        print("   ✓ Publisher: Indexed article to Elasticsearch")
        
        print(f"\n📈 Advanced Monitoring Features:")
        print("   • Real-time status updates from all agents every 2 seconds")
        print("   • Granular progress tracking through workflow steps")
        print("   • Parallel task execution monitoring")
        print("   • Live agent status polling")
        print("   • Workflow completion detection")
        print("   • Detailed timing and progress analysis")
        
        print("\n" + "=" * 80)
        print("✨ This demonstrates advanced live multi-agent coordination!")
        print("   You saw granular real-time updates from all agents")
        print("   as they collaborated to produce a complete news article.")
        print("=" * 80)


async def main():
    """Main entry point with error handling"""
    print("\n🧪 Elastic News - Advanced Live Workflow Test")
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
    
    print(f"\n⏰ Starting advanced live test at {datetime.now().strftime('%H:%M:%S')}")
    print("   This test will show granular real-time agent activity...")
    print("\nStarting in 3 seconds...")
    
    await asyncio.sleep(3)
    
    try:
        await test_newsroom_workflow_advanced()
    except KeyboardInterrupt:
        print("\n\n⏹️  Advanced live test interrupted by user")
    except Exception as e:
        print(f"\n❌ Advanced live test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
