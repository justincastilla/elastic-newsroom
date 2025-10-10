#!/usr/bin/env node

/**
 * Simple test to check current Researcher status
 * This test just checks what the current status is without starting a new workflow
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
    // Handle both string and object formats for waiting_status
    let reporterWaiting = false;
    if (typeof status.reporter?.waiting_status === 'string') {
      reporterWaiting = status.reporter.waiting_status === 'researcher_archivist' || 
                       status.reporter.waiting_status === 'researcher';
    } else if (typeof status.reporter?.waiting_status === 'object') {
      // Check if any story has researcher_archivist waiting status
      const waitingStatuses = Object.values(status.reporter.waiting_status);
      reporterWaiting = waitingStatuses.includes('researcher_archivist') || 
                       waitingStatuses.includes('researcher');
    }
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

async function testCurrentStatus() {
  console.log('🔍 Testing Current Researcher Status');
  console.log('====================================');
  
  try {
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
    
    console.log('\n📋 Current Agent Status:');
    console.log('Reporter waiting_status:', status.reporter?.waiting_status);
    console.log('Reporter waiting_status type:', typeof status.reporter?.waiting_status);
    console.log('Researcher research_history length:', status.researcher?.research_history?.length);
    if (status.researcher?.research_history?.length > 0) {
      const latest = status.researcher.research_history[status.researcher.research_history.length - 1];
      console.log('Latest research completed_at:', latest.completed_at);
      console.log('Latest research query:', latest.query);
    }
    
    // Test Researcher status with current data
    const researcherStatus = simulateResearcherStatus(status);
    console.log(`\n🎯 Current Researcher Status: ${researcherStatus}`);
    
    // Determine what the status should be
    const hasResearch = status.researcher?.research_history?.length > 0;
    const researchCompleted = hasResearch && status.researcher.research_history[status.researcher.research_history.length - 1].completed_at;
    // Check if Reporter is waiting for Researcher (handle both string and object formats)
    let reporterWaiting = false;
    if (typeof status.reporter?.waiting_status === 'string') {
      reporterWaiting = status.reporter.waiting_status === 'researcher_archivist' || 
                       status.reporter.waiting_status === 'researcher';
    } else if (typeof status.reporter?.waiting_status === 'object') {
      const waitingStatuses = Object.values(status.reporter.waiting_status);
      reporterWaiting = waitingStatuses.includes('researcher_archivist') || 
                       waitingStatuses.includes('researcher');
    }
    
    console.log('\n📊 Analysis:');
    console.log(`Has research: ${hasResearch}`);
    console.log(`Research completed: ${researchCompleted}`);
    console.log(`Reporter waiting: ${reporterWaiting}`);
    
    if (reporterWaiting) {
      console.log('✅ Expected: ACTIVE (Reporter is waiting for Researcher)');
    } else if (hasResearch && !researchCompleted) {
      console.log('✅ Expected: ACTIVE (Research is in progress)');
    } else {
      console.log('✅ Expected: IDLE (No active research)');
    }
    
    console.log(`Actual: ${researcherStatus.toUpperCase()}`);
    
    if ((reporterWaiting || (hasResearch && !researchCompleted)) && researcherStatus === 'active') {
      console.log('\n🎉 SUCCESS: Researcher card should be LIGHTING UP!');
      return true;
    } else if (!reporterWaiting && researchCompleted && researcherStatus === 'idle') {
      console.log('\n🎉 SUCCESS: Researcher card correctly shows idle');
      return true;
    } else {
      console.log('\n❌ ISSUE: Researcher status detection may need adjustment');
      return false;
    }
    
  } catch (error) {
    console.error('❌ Error testing current status:', error.message);
    return false;
  }
}

async function main() {
  console.log('🚀 Researcher Current Status Test');
  console.log('==================================');
  
  const testPassed = await testCurrentStatus();
  
  console.log('\n📊 Test Result');
  console.log('===============');
  console.log(`Test: ${testPassed ? '✅ PASSED' : '❌ FAILED'}`);
  
  if (testPassed) {
    console.log('\n🎉 Researcher status detection is working correctly!');
  } else {
    console.log('\n💥 Researcher status detection needs attention.');
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { simulateResearcherStatus, testCurrentStatus };
