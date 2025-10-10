#!/usr/bin/env node

/**
 * Comprehensive test to verify Researcher agent card lights up during workflow
 * This test simulates the actual workflow and verifies UI status detection
 */

const axios = require('axios');

const AGENT_URLS = {
  newsChief: 'http://localhost:8080',
  reporter: 'http://localhost:8081',
  editor: 'http://localhost:8082',
  researcher: 'http://localhost:8083',
  publisher: 'http://localhost:8084'
};

// Simulate the AgentStatus component logic for Researcher
function simulateResearcherStatus(status) {
  console.log('\n=== RESEARCHER STATUS SIMULATION ===');
  console.log('Input status:', JSON.stringify(status, null, 2));
  
  if (!status.researcher?.research_history?.length) {
    console.log('Researcher: No research history, returning idle');
    return 'idle';
  }
  
  const latestResearch = status.researcher.research_history[status.researcher.research_history.length - 1];
  
  // Debug logging
  console.log('Researcher latest research:', latestResearch);
  console.log('Researcher status check - completed_at:', latestResearch.completed_at);
  console.log('Researcher status check - status:', latestResearch.status);
  
  // Check if Reporter is waiting for Researcher (this is a more reliable indicator)
  const reporterWaiting = status.reporter?.waiting_status === 'researcher_archivist' || 
                         status.reporter?.waiting_status === 'researcher';
  console.log('Researcher status check - reporterWaiting:', reporterWaiting);
  
  // If Reporter is waiting for Researcher, show as active
  if (reporterWaiting) {
    console.log('Researcher: Reporter is waiting, returning active');
    return 'active';
  }
  
  // If research is completed (has completed_at timestamp), show as idle
  if (latestResearch.completed_at) {
    console.log('Researcher: Research completed, returning idle');
    return 'idle';
  }
  
  // If research is in progress (no completed_at), show as active
  if (!latestResearch.completed_at) {
    console.log('Researcher: Research in progress, returning active');
    return 'active';
  }
  
  console.log('Researcher: Default case, returning idle');
  return 'idle';
}

async function testResearcherWorkflow() {
  console.log('🧪 Testing Researcher Workflow Status Detection');
  console.log('===============================================');
  
  // Test Case 1: Reporter waiting for Researcher (should be ACTIVE)
  console.log('\n📋 Test Case 1: Reporter waiting for Researcher');
  const status1 = {
    reporter: {
      waiting_status: 'researcher_archivist',
      assignment: { reporter_status: 'researching' }
    },
    researcher: {
      research_history: [
        {
          research_id: 'research_123',
          query: 'Test question',
          completed_at: null
        }
      ]
    }
  };
  
  const result1 = simulateResearcherStatus(status1);
  if (result1 !== 'active') {
    console.error('❌ FAILED: Expected active when Reporter is waiting, got', result1);
    return false;
  }
  console.log('✅ PASSED: Researcher shows as active when Reporter is waiting');
  
  // Test Case 2: Research in progress (should be ACTIVE)
  console.log('\n📋 Test Case 2: Research in progress');
  const status2 = {
    reporter: {
      waiting_status: 'none',
      assignment: { reporter_status: 'researching' }
    },
    researcher: {
      research_history: [
        {
          research_id: 'research_123',
          query: 'Test question',
          completed_at: null
        }
      ]
    }
  };
  
  const result2 = simulateResearcherStatus(status2);
  if (result2 !== 'active') {
    console.error('❌ FAILED: Expected active when research in progress, got', result2);
    return false;
  }
  console.log('✅ PASSED: Researcher shows as active when research is in progress');
  
  // Test Case 3: Research completed (should be IDLE)
  console.log('\n📋 Test Case 3: Research completed');
  const status3 = {
    reporter: {
      waiting_status: 'none',
      assignment: { reporter_status: 'writing' }
    },
    researcher: {
      research_history: [
        {
          research_id: 'research_123',
          query: 'Test question',
          completed_at: '2025-10-10T16:00:50.887298'
        }
      ]
    }
  };
  
  const result3 = simulateResearcherStatus(status3);
  if (result3 !== 'idle') {
    console.error('❌ FAILED: Expected idle when research completed, got', result3);
    return false;
  }
  console.log('✅ PASSED: Researcher shows as idle when research is completed');
  
  // Test Case 4: No research history (should be IDLE)
  console.log('\n📋 Test Case 4: No research history');
  const status4 = {
    reporter: {
      waiting_status: 'none',
      assignment: { reporter_status: 'researching' }
    },
    researcher: {
      research_history: []
    }
  };
  
  const result4 = simulateResearcherStatus(status4);
  if (result4 !== 'idle') {
    console.error('❌ FAILED: Expected idle when no research history, got', result4);
    return false;
  }
  console.log('✅ PASSED: Researcher shows as idle when no research history');
  
  return true;
}

async function testWithRealWorkflow() {
  console.log('\n🚀 Testing with Real Workflow');
  console.log('==============================');
  
  try {
    // Start a new workflow
    console.log('📝 Starting new workflow...');
    const storyData = {
      topic: 'AI Testing',
      angle: 'Testing researcher status detection',
      target_length: 500
    };
    
    const assignResponse = await axios.post(`${AGENT_URLS.newsChief}/assign-story`, { 
      action: 'assign_story',
      ...storyData 
    }, { timeout: 10000 });
    console.log('Story assigned:', assignResponse.data);
    
    if (assignResponse.data.status !== 'success') {
      throw new Error('Failed to assign story');
    }
    
    const storyId = assignResponse.data.story_id;
    console.log('Story ID:', storyId);
    
    // Wait a moment for the workflow to start
    console.log('⏳ Waiting for workflow to start...');
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Get status from all agents
    console.log('📊 Getting agent statuses...');
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
    
    console.log('\n📋 Real Agent Status:');
    console.log('Reporter waiting_status:', status.reporter?.waiting_status);
    console.log('Researcher research_history length:', status.researcher?.research_history?.length);
    if (status.researcher?.research_history?.length > 0) {
      const latest = status.researcher.research_history[status.researcher.research_history.length - 1];
      console.log('Latest research completed_at:', latest.completed_at);
    }
    
    // Test Researcher status with real data
    const researcherStatus = simulateResearcherStatus(status);
    console.log(`\n🎯 Real Researcher Status: ${researcherStatus}`);
    
    // Expected behavior: Should be active if Reporter is waiting or research is in progress
    const expectedActive = status.reporter?.waiting_status === 'researcher_archivist' || 
                          (status.researcher?.research_history?.length > 0 && 
                           !status.researcher.research_history[status.researcher.research_history.length - 1].completed_at);
    
    console.log(`Expected active: ${expectedActive}`);
    console.log(`Actual status: ${researcherStatus}`);
    
    if (expectedActive && researcherStatus === 'active') {
      console.log('✅ SUCCESS: Researcher card should be LIGHTING UP!');
      return true;
    } else if (!expectedActive && researcherStatus === 'idle') {
      console.log('✅ SUCCESS: Researcher card correctly shows idle');
      return true;
    } else {
      console.log('❌ FAILURE: Researcher status detection is not working correctly');
      return false;
    }
    
  } catch (error) {
    console.error('❌ Error testing with real workflow:', error.message);
    return false;
  }
}

async function main() {
  console.log('🚀 Researcher Workflow Test');
  console.log('============================');
  
  // Test with mock data
  const mockTestPassed = await testResearcherWorkflow();
  
  // Test with real workflow
  const realTestPassed = await testWithRealWorkflow();
  
  console.log('\n📊 Final Test Results');
  console.log('======================');
  console.log(`Mock data test: ${mockTestPassed ? '✅ PASSED' : '❌ FAILED'}`);
  console.log(`Real workflow test: ${realTestPassed ? '✅ PASSED' : '❌ FAILED'}`);
  
  if (mockTestPassed && realTestPassed) {
    console.log('\n🎉 ALL TESTS PASSED! Researcher card should be lighting up correctly!');
  } else {
    console.log('\n💥 SOME TESTS FAILED! Researcher status detection needs fixing.');
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { simulateResearcherStatus, testResearcherWorkflow };
