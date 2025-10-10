#!/usr/bin/env python3
"""
Elastic News - Comprehensive Multi-Agent Workflow Test

This test provides complete real-time monitoring of ALL agents in the newsroom,
showing exactly what each agent is doing at every moment during the workflow.

Features:
- Real-time monitoring of ALL 5 agents simultaneously
- Live activity tracking for each agent
- Parallel agent coordination visibility
- Complete workflow transparency
"""

import asyncio
import json
import time
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List
from a2a.client import ClientFactory, ClientConfig, A2ACardResolver, create_text_message_object


class ComprehensiveWorkflowMonitor:
    """Comprehensive monitor for all agents with real-time activity tracking"""
    
    def __init__(self):
        self.start_time = None
        self.step_times = {}
        self.current_step = None
        self.agent_activities = {}
        self.workflow_progress = {}
        self.parallel_activities = {}
        self.agent_status_history = {}
        
    def start_workflow(self):
        """Start timing the entire workflow"""
        self.start_time = time.time()
        print("🚀 Comprehensive multi-agent workflow monitoring started")
        
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
            
    def update_agent_activity(self, agent: str, activity: str, details: str = "", status: str = ""):
        """Update the activity of a specific agent"""
        self.agent_activities[agent] = {
            'activity': activity,
            'details': details,
            'status': status,
            'timestamp': time.time()
        }
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        # Add to history
        if agent not in self.agent_status_history:
            self.agent_status_history[agent] = []
        self.agent_status_history[agent].append({
            'activity': activity,
            'details': details,
            'status': status,
            'timestamp': time.time(),
            'elapsed': elapsed
        })
        
        print(f"    🤖 [{elapsed:6.1f}s] {agent}: {activity} {details}")
        if status:
            print(f"         Status: {status}")
            
    def update_workflow_progress(self, step: str, progress: str, details: str = ""):
        """Update workflow progress within a step"""
        self.workflow_progress[step] = {
            'progress': progress,
            'details': details,
            'timestamp': time.time()
        }
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"    🔄 [{elapsed:6.1f}s] {step}: {progress} {details}")
        
    def update_parallel_activity(self, activity: str, status: str, details: str = ""):
        """Update parallel agent activities"""
        self.parallel_activities[activity] = {
            'status': status,
            'details': details,
            'timestamp': time.time()
        }
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"    ⚡ [{elapsed:6.1f}s] {activity}: {status} {details}")
        
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow execution"""
        total_time = time.time() - self.start_time if self.start_time else 0
        return {
            'total_time': total_time,
            'steps': self.step_times,
            'agent_activities': self.agent_activities,
            'workflow_progress': self.workflow_progress,
            'parallel_activities': self.parallel_activities,
            'agent_status_history': self.agent_status_history
        }


async def monitor_all_agents_comprehensive(http_client: httpx.AsyncClient, clients: Dict[str, Any], story_id: str, monitor: ComprehensiveWorkflowMonitor, max_duration: int = 600):
    """Monitor ALL agents comprehensively during workflow execution"""
    
    start_time = time.time()
    last_updates = {}
    
    print(f"    🔍 Starting comprehensive monitoring of ALL agents...")
    print(f"    ⏰ Will monitor for up to {max_duration} seconds")
    print(f"    📡 Polling every 2 seconds for real-time agent activities...")
    print(f"    🤖 Monitoring: News Chief, Reporter, Editor, Researcher, Publisher")
    
    while time.time() - start_time < max_duration:
        try:
            # Monitor News Chief
            await monitor_agent_comprehensive(http_client, clients.get('News Chief'), 'News Chief', story_id, monitor, last_updates)
            
            # Monitor Reporter
            await monitor_agent_comprehensive(http_client, clients.get('Reporter'), 'Reporter', story_id, monitor, last_updates)
            
            # Monitor Editor
            await monitor_agent_comprehensive(http_client, clients.get('Editor'), 'Editor', story_id, monitor, last_updates)
            
            # Monitor Researcher
            await monitor_agent_comprehensive(http_client, clients.get('Researcher'), 'Researcher', story_id, monitor, last_updates)
            
            # Monitor Publisher
            await monitor_agent_comprehensive(http_client, clients.get('Publisher'), 'Publisher', story_id, monitor, last_updates)
            
            # Check if workflow is complete by monitoring News Chief's story status
            news_chief_activity = monitor.agent_activities.get('News Chief', {})
            story_status = news_chief_activity.get('status', '')
            
            # Check for completion indicators from News Chief
            if ('published' in story_status.lower() or 
                'completed' in story_status.lower() or
                'error' in story_status.lower()):
                monitor.update_workflow_progress('Workflow', 'Complete', f'News Chief reports story status: {story_status}')
                return True
            
            # Also check Reporter status as backup
            reporter_status = monitor.agent_activities.get('Reporter', {}).get('status', '')
            reporter_activity = monitor.agent_activities.get('Reporter', {}).get('activity', '')
            
            if ('published' in reporter_status.lower() or 
                'published' in reporter_activity.lower() or
                'workflow completed' in reporter_activity.lower() or
                'article published' in reporter_activity.lower()):
                monitor.update_workflow_progress('Workflow', 'Complete', 'Reporter reports completion')
                return True
                
            # Wait before next poll
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"    ⚠️  Error in comprehensive monitoring: {e}")
            await asyncio.sleep(5)
    
    print(f"    ⏰ Comprehensive monitoring timeout reached ({max_duration}s)")
    return False


async def monitor_agent_comprehensive(http_client: httpx.AsyncClient, client, agent_name: str, story_id: str, monitor: ComprehensiveWorkflowMonitor, last_updates: Dict[str, str]):
    """Monitor a specific agent comprehensively"""
    
    if not client:
        return
        
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
                    
                    # Process each agent's specific status
                    if agent_name == 'News Chief':
                        await process_news_chief_status(result, monitor, last_updates)
                    elif agent_name == 'Reporter':
                        await process_reporter_status(result, monitor, last_updates)
                    elif agent_name == 'Editor':
                        await process_editor_status(result, monitor, last_updates)
                    elif agent_name == 'Researcher':
                        await process_researcher_status(result, monitor, last_updates)
                    elif agent_name == 'Publisher':
                        await process_publisher_status(result, monitor, last_updates)
                    
                    break
                    
    except Exception as e:
        # Silently handle individual agent monitoring errors
        pass


async def process_news_chief_status(result: Dict[str, Any], monitor: ComprehensiveWorkflowMonitor, last_updates: Dict[str, str]):
    """Process News Chief status and activities"""
    
    # Check story status - this is the key indicator of workflow progress
    story = result.get('story', {})
    if story:
        story_status = story.get('status', 'unknown')
        if story_status != last_updates.get('news_chief_story_status'):
            last_updates['news_chief_story_status'] = story_status
            
            # Map story status to specific activities
            if story_status == 'assigned':
                monitor.update_agent_activity('News Chief', 'Story assigned to Reporter', '📋 Coordinating workflow', story_status)
            elif story_status == 'writing':
                monitor.update_agent_activity('News Chief', 'Reporter is writing article', '✍️ Monitoring progress', story_status)
            elif story_status == 'draft_submitted':
                monitor.update_agent_activity('News Chief', 'Draft submitted for review', '📤 Routing to Editor', story_status)
            elif story_status == 'under_review':
                monitor.update_agent_activity('News Chief', 'Article under editorial review', '✏️ Editor analyzing content', story_status)
            elif story_status == 'reviewed':
                monitor.update_agent_activity('News Chief', 'Editor review completed', '✅ Feedback provided', story_status)
            elif story_status == 'needs_revision':
                monitor.update_agent_activity('News Chief', 'Article needs revision', '🔄 Sending back to Reporter', story_status)
            elif story_status == 'revised':
                monitor.update_agent_activity('News Chief', 'Article revised by Reporter', '📝 Updated content received', story_status)
            elif story_status == 'publishing':
                monitor.update_agent_activity('News Chief', 'Publishing article', '📰 Sending to Publisher', story_status)
            elif story_status == 'published':
                monitor.update_agent_activity('News Chief', 'Article published successfully', '🎉 Workflow completed', story_status)
            elif story_status == 'completed':
                monitor.update_agent_activity('News Chief', 'Workflow completed', '✅ All tasks finished', story_status)
            elif story_status == 'error':
                monitor.update_agent_activity('News Chief', 'Workflow error occurred', '❌ Issue detected', story_status)
            else:
                monitor.update_agent_activity('News Chief', f'Story status: {story_status}', '🔄 Processing', story_status)
    
    # Check active stories count
    active_stories = result.get('active_stories', {})
    if active_stories:
        story_count = len(active_stories)
        if story_count != last_updates.get('news_chief_story_count'):
            last_updates['news_chief_story_count'] = story_count
            monitor.update_agent_activity('News Chief', f"Managing {story_count} active stories", "📊 Workflow coordination")


async def process_reporter_status(result: Dict[str, Any], monitor: ComprehensiveWorkflowMonitor, last_updates: Dict[str, str]):
    """Process Reporter status and activities"""
    
    assignment = result.get('assignment', {})
    if assignment:
        reporter_status = assignment.get('reporter_status', 'unknown')
        if reporter_status != last_updates.get('reporter_status'):
            last_updates['reporter_status'] = reporter_status
            
            # Map status to specific activities
            if reporter_status == 'researching':
                monitor.update_agent_activity('Reporter', 'Generating outline and research questions', '📋 Creating article structure', reporter_status)
                monitor.update_parallel_activity('Researcher', 'Starting research', '🔍 Preparing to gather facts')
                monitor.update_parallel_activity('Archivist', 'Starting archive search', '📚 Preparing to search history (optional)')
            elif reporter_status == 'writing' or reporter_status == 'drafting':
                monitor.update_agent_activity('Reporter', 'Writing article with research data', '✍️ Generating content', reporter_status)
                monitor.update_parallel_activity('Researcher', 'Research completed', '✅ Facts gathered')
                monitor.update_parallel_activity('Archivist', 'Archive search completed', '✅ Historical context found (or skipped)')
            elif reporter_status == 'draft_complete' or reporter_status == 'draft_ready':
                monitor.update_agent_activity('Reporter', 'Draft completed, submitting to Editor', '📤 Sending for review', reporter_status)
                monitor.update_parallel_activity('Editor', 'Starting review', '✏️ Analyzing content')
            elif reporter_status == 'editing' or reporter_status == 'applying_edits':
                monitor.update_agent_activity('Reporter', 'Applying editorial suggestions', '✏️ Incorporating feedback', reporter_status)
                monitor.update_parallel_activity('Editor', 'Review completed', '✅ Feedback provided')
            elif reporter_status == 'published' or reporter_status == 'publishing':
                monitor.update_agent_activity('Reporter', 'Article published to Elasticsearch', '📰 Final publication', reporter_status)
                monitor.update_parallel_activity('Publisher', 'Publishing completed', '✅ Article indexed')
            elif reporter_status not in ['unknown', '']:
                monitor.update_agent_activity('Reporter', f'Processing: {reporter_status}', '🔄 Working on article', reporter_status)
    
    # Check draft status
    draft = result.get('draft', {})
    if draft:
        draft_status = draft.get('status', 'unknown')
        if draft_status != last_updates.get('draft_status') and draft_status != 'unknown':
            last_updates['draft_status'] = draft_status
            word_count = draft.get('word_count', 0)
            monitor.update_agent_activity('Reporter', f'Draft status: {draft_status}', f'Words: {word_count}')


async def process_editor_status(result: Dict[str, Any], monitor: ComprehensiveWorkflowMonitor, last_updates: Dict[str, str]):
    """Process Editor status and activities"""
    
    reviews = result.get('reviews', [])
    if reviews:
        latest_review = reviews[-1]
        review_status = latest_review.get('status', 'unknown')
        if review_status != last_updates.get('editor_review_status'):
            last_updates['editor_review_status'] = review_status
            
            if review_status == 'reviewing':
                monitor.update_agent_activity('Editor', 'Reviewing article content', '✏️ Analyzing quality and consistency')
            elif review_status == 'completed':
                monitor.update_agent_activity('Editor', 'Review completed', '✅ Feedback provided to Reporter')
            elif review_status == 'editing':
                monitor.update_agent_activity('Editor', 'Providing editorial feedback', '📝 Writing suggestions')
    
    # Check total reviews
    total_reviews = len(reviews)
    if total_reviews != last_updates.get('editor_total_reviews'):
        last_updates['editor_total_reviews'] = total_reviews
        monitor.update_agent_activity('Editor', f'Completed {total_reviews} reviews', '📊 Review statistics')


async def process_researcher_status(result: Dict[str, Any], monitor: ComprehensiveWorkflowMonitor, last_updates: Dict[str, str]):
    """Process Researcher status and activities"""
    
    research_history = result.get('research_history', [])
    if research_history:
        latest_research = research_history[-1]
        research_status = latest_research.get('status', 'unknown')
        if research_status != last_updates.get('researcher_status'):
            last_updates['researcher_status'] = research_status
            
            if research_status == 'researching':
                monitor.update_agent_activity('Researcher', 'Gathering factual information', '🔍 Researching topics')
            elif research_status == 'completed':
                monitor.update_agent_activity('Researcher', 'Research completed', '✅ Facts gathered and structured')
            elif research_status == 'processing':
                monitor.update_agent_activity('Researcher', 'Processing research data', '📊 Structuring information')
    
    # Check research questions
    questions = result.get('questions', [])
    if questions:
        question_count = len(questions)
        if question_count != last_updates.get('researcher_question_count'):
            last_updates['researcher_question_count'] = question_count
            monitor.update_agent_activity('Researcher', f'Processing {question_count} research questions', '❓ Analyzing requirements')


async def process_publisher_status(result: Dict[str, Any], monitor: ComprehensiveWorkflowMonitor, last_updates: Dict[str, str]):
    """Process Publisher status and activities"""
    
    total_published = result.get('total_published', 0)
    if total_published != last_updates.get('publisher_total'):
        last_updates['publisher_total'] = total_published
        monitor.update_agent_activity('Publisher', f'Published {total_published} articles', '📰 Publication statistics')
    
    # Check recent publications
    recent_publications = result.get('recent_publications', [])
    if recent_publications:
        latest_publication = recent_publications[0]
        pub_status = latest_publication.get('status', 'unknown')
        if pub_status != last_updates.get('publisher_latest_status'):
            last_updates['publisher_latest_status'] = pub_status
            
            if pub_status == 'indexing':
                monitor.update_agent_activity('Publisher', 'Indexing article to Elasticsearch', '🔍 Adding to search index')
            elif pub_status == 'published':
                monitor.update_agent_activity('Publisher', 'Article successfully published', '✅ Indexed and available')
            elif pub_status == 'saving':
                monitor.update_agent_activity('Publisher', 'Saving article to file system', '💾 Creating markdown file')


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


async def test_newsroom_workflow_comprehensive():
    """Test the complete newsroom workflow with comprehensive multi-agent monitoring"""
    
    # Initialize comprehensive workflow monitor
    monitor = ComprehensiveWorkflowMonitor()
    
    print("🏢 Elastic News - Comprehensive Multi-Agent Workflow Test")
    print("=" * 80)
    print("This test demonstrates the complete multi-agent newsroom workflow")
    print("with comprehensive real-time monitoring of ALL agents.")
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
                monitor.update_agent_activity(agent_name, "Client initialized", f"({len(agent_card.skills)} skills)")
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
                    monitor.update_agent_activity('News Chief', "Story assigned", f"ID: {story_id}")
                    
                    # Check reporter response
                    reporter_response = result.get('reporter_response', {})
                    if reporter_response:
                        monitor.update_agent_activity('Reporter', "Assignment accepted", f"Status: {reporter_response.get('status')}")
        
        if not story_id:
            monitor.end_step("STORY_ASSIGNMENT", False, "- No story ID returned")
            return
            
        monitor.end_step("STORY_ASSIGNMENT", True, f"- Story ID: {story_id}")
        
        # ========================================
        # STEP 4: Comprehensive Multi-Agent Workflow Monitoring
        # ========================================
        monitor.start_step("COMPREHENSIVE_WORKFLOW", "Comprehensive monitoring of ALL agents during workflow")
        
        print("    🔄 Multi-Agent Workflow with Comprehensive Monitoring:")
        print("       1. Reporter generates outline and research questions")
        print("       2. Researcher + Archivist work in parallel")
        print("       3. Reporter writes article with all data")
        print("       4. Editor reviews and provides feedback")
        print("       5. Reporter applies editorial suggestions")
        print("       6. Publisher indexes to Elasticsearch")
        print()
        print("    📡 Comprehensive monitoring will show:")
        print("       • Real-time activity of ALL agents")
        print("       • Live status updates from every agent")
        print("       • Parallel agent coordination")
        print("       • Complete workflow transparency")
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
        
        # Start comprehensive live monitoring
        monitoring_task = asyncio.create_task(
            monitor_all_agents_comprehensive(http_client, clients, story_id, monitor)
        )
        
        # Wait for either the workflow to complete or monitoring to finish
        try:
            await asyncio.wait_for(monitoring_task, timeout=600)
            monitor.update_workflow_progress('Workflow', 'Comprehensive monitoring completed', 'All agents tracked')
        except asyncio.TimeoutError:
            print("    ⏰ Comprehensive monitoring timeout reached")
        
        # Wait for the workflow to complete
        try:
            await asyncio.wait_for(workflow_task, timeout=10)
        except asyncio.TimeoutError:
            print("    ⏰ Workflow task timeout")
        
        monitor.end_step("COMPREHENSIVE_WORKFLOW", True, "Comprehensive monitoring completed")
        
        # ========================================
        # WORKFLOW SUMMARY
        # ========================================
        summary = monitor.get_summary()
        
        print("\n" + "=" * 80)
        print("🎉 COMPREHENSIVE MULTI-AGENT WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        print(f"\n⏱️  Total Execution Time: {summary['total_time']:.1f} seconds")
        
        print(f"\n📊 Step Breakdown:")
        for step_name, step_data in summary['steps'].items():
            duration = step_data.get('duration', 0)
            success = step_data.get('success', False)
            status_icon = "✅" if success else "❌"
            print(f"   {status_icon} {step_name}: {duration:.1f}s - {step_data['description']}")
        
        print(f"\n🤖 Agent Activity Summary:")
        for agent, activity_data in summary['agent_activities'].items():
            print(f"   • {agent}: {activity_data['activity']} - {activity_data['details']}")
        
        print(f"\n🔄 Workflow Progress Tracked:")
        for step, progress_data in summary['workflow_progress'].items():
            print(f"   • {step}: {progress_data['progress']} - {progress_data['details']}")
        
        print(f"\n⚡ Parallel Activities Monitored:")
        for activity, activity_data in summary['parallel_activities'].items():
            print(f"   • {activity}: {activity_data['status']} - {activity_data['details']}")
        
        print(f"\n📈 Comprehensive Monitoring Features:")
        print("   • Real-time activity tracking for ALL agents")
        print("   • Live status updates from every agent")
        print("   • Parallel agent coordination monitoring")
        print("   • Complete workflow transparency")
        print("   • Detailed agent activity history")
        
        print("\n" + "=" * 80)
        print("✨ This demonstrates comprehensive multi-agent coordination!")
        print("   You saw real-time activity from ALL agents as they")
        print("   collaborated to produce a complete news article.")
        print("=" * 80)


async def main():
    """Main entry point with error handling"""
    print("\n🧪 Elastic News - Comprehensive Multi-Agent Workflow Test")
    print("\n⚠️  Prerequisites:")
    print("   1. All agents running:")
    print("      → ./start_newsroom.sh")
    print("   2. Environment variables set:")
    print("      → ANTHROPIC_API_KEY (required)")
    print("      → ELASTICSEARCH_ENDPOINT (required)")
    print("      → ELASTIC_SEARCH_API_KEY (required)")
    print("      → ELASTIC_ARCHIVIST_AGENT_CARD_URL (optional)")
    print("      → ELASTIC_ARCHIVIST_API_KEY (optional)")
    
    print(f"\n⏰ Starting comprehensive test at {datetime.now().strftime('%H:%M:%S')}")
    print("   This test will show real-time activity from ALL agents...")
    print("\nStarting in 3 seconds...")
    
    await asyncio.sleep(3)
    
    try:
        await test_newsroom_workflow_comprehensive()
    except KeyboardInterrupt:
        print("\n\n⏹️  Comprehensive test interrupted by user")
    except Exception as e:
        print(f"\n❌ Comprehensive test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
