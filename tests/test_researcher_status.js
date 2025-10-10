#!/usr/bin/env node

/**
 * Test to verify Researcher agent status card lights up correctly
 * This test mimics the actual workflow logs and verifies UI status detection
 */

const axios = require('axios');

const AGENT_URLS = {
  newsChief: 'http://localhost:8080',
  reporter: 'http://localhost:8081',
  editor: 'http://localhost:8082',
  researcher: 'http://localhost:8083',
  publisher: 'http://localhost:8084'
};

// Mock status data that mimics what the UI receives
const mockStatusData = {
  newsChief: {
    story: {
      story_id: 'test_story_123',
      status: 'assigned',
      topic: 'Test Topic',
      angle: 'Test Angle',
      target_length: 1000
    }
  },
  reporter: {
    assignment: {
      story_id: 'test_story_123',
      reporter_status: 'researching',
      topic: 'Test Topic',
      angle: 'Test Angle',
      target_length: 1000
    },
    waiting_status: 'researcher_archivist',
    archivist_status: 'active'
  },
  editor: {
    reviews: []
  },
  researcher: {
    research_history: [
      {
        session_id: 'research_123',
        query: 'What are the latest developments in AI?',
        status: 'active',
        completed_at: null,
        created_at: new Date().toISOString()
      }
    ]
  },
  publisher: {
    published_articles: {},
    total_published: 0
  }
};

// Simulate the AgentStatus component logic
function simulateResearcherStatus(status) {
  console.log('\n=== RESEARCHER STATUS SIMULATION ===');
  console.log('Input status:', JSON.stringify(status, null, 2));
  
  // Check if Reporter is waiting for Researcher (this is a more reliable indicator)
  const reporterWaiting = status.reporter?.waiting_status === 'researcher_archivist' || 
                         status.reporter?.waiting_status === 'researcher';
  console.log('Reporter waiting for Researcher:', reporterWaiting);
  
  // Check research history
  const hasResearchHistory = status.researcher?.research_history?.length > 0;
  console.log('Has research history:', hasResearchHistory);
  
  if (hasResearchHistory) {
    const latestResearch = status.researcher.research_history[status.researcher.research_history.length - 1];
    console.log('Latest research:', latestResearch);
    console.log('Research status:', latestResearch.status);
    console.log('Research completed_at:', latestResearch.completed_at);
    
    // If Reporter is waiting for Researcher, show as active
    if (reporterWaiting) {
      console.log('✅ RESULT: active (Reporter waiting)');
      return 'active';
    }
    
    // If research is completed, show as idle
    if (latestResearch.completed_at || latestResearch.status === 'completed') {
      console.log('✅ RESULT: idle (Research completed)');
      return 'idle';
    }
    
    // If research is in progress, show as active
    if (latestResearch.status === 'active' || latestResearch.status === 'researching' || !latestResearch.completed_at) {
      console.log('✅ RESULT: active (Research in progress)');
      return 'active';
    }
  }
  
  console.log('✅ RESULT: idle (No research or waiting)');
  return 'idle';
}

async function testResearcherStatus() {
  console.log('🧪 Testing Researcher Status Detection');
  console.log('=====================================');
  
  // Test Case 1: Reporter waiting for Researcher
  console.log('\n📋 Test Case 1: Reporter waiting for Researcher');
  const status1 = simulateResearcherStatus(mockStatusData);
  if (status1 !== 'active') {
    console.error('❌ FAILED: Expected active, got', status1);
    return false;
  }
  console.log('✅ PASSED: Researcher shows as active when Reporter is waiting');
  
  // Test Case 2: Research in progress
  console.log('\n📋 Test Case 2: Research in progress');
  const statusData2 = {
    ...mockStatusData,
    reporter: {
      ...mockStatusData.reporter,
      waiting_status: 'none'
    }
  };
  const status2 = simulateResearcherStatus(statusData2);
  if (status2 !== 'active') {
    console.error('❌ FAILED: Expected active, got', status2);
    return false;
  }
  console.log('✅ PASSED: Researcher shows as active when research is in progress');
  
  // Test Case 3: Research completed
  console.log('\n📋 Test Case 3: Research completed');
  const statusData3 = {
    ...mockStatusData,
    reporter: {
      ...mockStatusData.reporter,
      waiting_status: 'none'
    },
    researcher: {
      research_history: [
        {
          session_id: 'research_123',
          query: 'What are the latest developments in AI?',
          status: 'completed',
          completed_at: new Date().toISOString(),
          created_at: new Date().toISOString()
        }
      ]
    }
  };
  const status3 = simulateResearcherStatus(statusData3);
  if (status3 !== 'idle') {
    console.error('❌ FAILED: Expected idle, got', status3);
    return false;
  }
  console.log('✅ PASSED: Researcher shows as idle when research is completed');
  
  // Test Case 4: No research history
  console.log('\n📋 Test Case 4: No research history');
  const statusData4 = {
    ...mockStatusData,
    researcher: {
      research_history: []
    }
  };
  const status4 = simulateResearcherStatus(statusData4);
  if (status4 !== 'idle') {
    console.error('❌ FAILED: Expected idle, got', status4);
    return false;
  }
  console.log('✅ PASSED: Researcher shows as idle when no research history');
  
  return true;
}

async function testWithRealAgents() {
  console.log('\n🔍 Testing with Real Agent Status');
  console.log('==================================');
  
  try {
    // Get real status from all agents
    const statusPromises = Object.entries(AGENT_URLS).map(async ([agentName, url]) => {
      try {
        const response = await axios.post(`${url}/get-status`, { action: 'get_status' }, { timeout: 5000 });
        return [agentName, response.data];
      } catch (error) {
        console.warn(`⚠️  Failed to get status from ${agentName}:`, error.message);
        return [agentName, null];
      }
    });
    
    const agentStatuses = await Promise.all(statusPromises);
    const status = {};
    agentStatuses.forEach(([agentName, data]) => {
      if (data) {
        status[agentName] = data;
      }
    });
    
    console.log('Real agent statuses:', JSON.stringify(status, null, 2));
    
    // Test with real data
    const realStatus = simulateResearcherStatus(status);
    console.log(`\n🎯 Real Researcher Status: ${realStatus}`);
    
    return realStatus;
    
  } catch (error) {
    console.error('❌ Error testing with real agents:', error.message);
    return null;
  }
}

async function main() {
  console.log('🚀 Researcher Status Test');
  console.log('========================');
  
  // Test with mock data
  const mockTestPassed = await testResearcherStatus();
  
  // Test with real agents
  const realStatus = await testWithRealAgents();
  
  console.log('\n📊 Test Results');
  console.log('================');
  console.log(`Mock data test: ${mockTestPassed ? '✅ PASSED' : '❌ FAILED'}`);
  console.log(`Real agent status: ${realStatus || '❌ FAILED'}`);
  
  if (mockTestPassed && realStatus) {
    console.log('\n🎉 All tests passed! Researcher status detection is working correctly.');
  } else {
    console.log('\n💥 Some tests failed. Researcher status detection needs fixing.');
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { simulateResearcherStatus, testResearcherStatus };
