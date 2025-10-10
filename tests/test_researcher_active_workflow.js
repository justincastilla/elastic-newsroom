#!/usr/bin/env node

/**
 * Test to verify Researcher card lights up during active workflow
 * This test simulates the exact conditions when Researcher should be active
 */

const axios = require('axios');

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

async function testActiveWorkflowScenarios() {
  console.log('🧪 Testing Active Workflow Scenarios');
  console.log('=====================================');
  
  // Scenario 1: Reporter waiting for Researcher (should be ACTIVE)
  console.log('\n📋 Scenario 1: Reporter waiting for Researcher');
  const status1 = {
    reporter: {
      waiting_status: 'researcher_archivist',
      assignment: { reporter_status: 'researching' }
    },
    researcher: {
      research_history: [
        {
          research_id: 'research_123',
          query: 'What are the latest AI developments?',
          completed_at: null
        }
      ]
    }
  };
  
  const result1 = simulateResearcherStatus(status1);
  console.log(`Result: ${result1}`);
  if (result1 !== 'active') {
    console.error('❌ FAILED: Expected active when Reporter is waiting');
    return false;
  }
  console.log('✅ PASSED: Researcher shows as active when Reporter is waiting');
  
  // Scenario 2: Research in progress (should be ACTIVE)
  console.log('\n📋 Scenario 2: Research in progress');
  const status2 = {
    reporter: {
      waiting_status: 'none',
      assignment: { reporter_status: 'researching' }
    },
    researcher: {
      research_history: [
        {
          research_id: 'research_123',
          query: 'What are the latest AI developments?',
          completed_at: null
        }
      ]
    }
  };
  
  const result2 = simulateResearcherStatus(status2);
  console.log(`Result: ${result2}`);
  if (result2 !== 'active') {
    console.error('❌ FAILED: Expected active when research is in progress');
    return false;
  }
  console.log('✅ PASSED: Researcher shows as active when research is in progress');
  
  // Scenario 3: Reporter waiting for researcher (different waiting status)
  console.log('\n📋 Scenario 3: Reporter waiting for researcher (different status)');
  const status3 = {
    reporter: {
      waiting_status: 'researcher',
      assignment: { reporter_status: 'researching' }
    },
    researcher: {
      research_history: [
        {
          research_id: 'research_123',
          query: 'What are the latest AI developments?',
          completed_at: null
        }
      ]
    }
  };
  
  const result3 = simulateResearcherStatus(status3);
  console.log(`Result: ${result3}`);
  if (result3 !== 'active') {
    console.error('❌ FAILED: Expected active when Reporter waiting for researcher');
    return false;
  }
  console.log('✅ PASSED: Researcher shows as active when Reporter waiting for researcher');
  
  return true;
}

async function testWithMockWorkflow() {
  console.log('\n🚀 Testing with Mock Workflow');
  console.log('==============================');
  
  // Simulate a complete workflow with different stages
  const workflowStages = [
    {
      name: 'Initial Assignment',
      status: {
        reporter: { waiting_status: 'none', assignment: { reporter_status: 'researching' } },
        researcher: { research_history: [] }
      },
      expected: 'idle'
    },
    {
      name: 'Reporter Waiting for Research',
      status: {
        reporter: { waiting_status: 'researcher_archivist', assignment: { reporter_status: 'researching' } },
        researcher: { research_history: [] }
      },
      expected: 'idle' // No research history yet
    },
    {
      name: 'Research Started',
      status: {
        reporter: { waiting_status: 'researcher_archivist', assignment: { reporter_status: 'researching' } },
        researcher: {
          research_history: [
            {
              research_id: 'research_123',
              query: 'What are the latest AI developments?',
              completed_at: null
            }
          ]
        }
      },
      expected: 'active'
    },
    {
      name: 'Research in Progress',
      status: {
        reporter: { waiting_status: 'none', assignment: { reporter_status: 'researching' } },
        researcher: {
          research_history: [
            {
              research_id: 'research_123',
              query: 'What are the latest AI developments?',
              completed_at: null
            }
          ]
        }
      },
      expected: 'active'
    },
    {
      name: 'Research Completed',
      status: {
        reporter: { waiting_status: 'none', assignment: { reporter_status: 'writing' } },
        researcher: {
          research_history: [
            {
              research_id: 'research_123',
              query: 'What are the latest AI developments?',
              completed_at: '2025-10-10T16:00:50.887298'
            }
          ]
        }
      },
      expected: 'idle'
    }
  ];
  
  let allPassed = true;
  
  for (const stage of workflowStages) {
    console.log(`\n📋 ${stage.name}`);
    const result = simulateResearcherStatus(stage.status);
    console.log(`Expected: ${stage.expected}, Actual: ${result}`);
    
    if (result === stage.expected) {
      console.log('✅ PASSED');
    } else {
      console.log('❌ FAILED');
      allPassed = false;
    }
  }
  
  return allPassed;
}

async function main() {
  console.log('🚀 Researcher Active Workflow Test');
  console.log('===================================');
  
  // Test active scenarios
  const activeTestPassed = await testActiveWorkflowScenarios();
  
  // Test mock workflow
  const workflowTestPassed = await testWithMockWorkflow();
  
  console.log('\n📊 Final Test Results');
  console.log('======================');
  console.log(`Active scenarios test: ${activeTestPassed ? '✅ PASSED' : '❌ FAILED'}`);
  console.log(`Mock workflow test: ${workflowTestPassed ? '✅ PASSED' : '❌ FAILED'}`);
  
  if (activeTestPassed && workflowTestPassed) {
    console.log('\n🎉 ALL TESTS PASSED! Researcher card should light up correctly during workflow!');
    console.log('\n💡 Key Points:');
    console.log('   - Researcher shows ACTIVE when Reporter is waiting for research');
    console.log('   - Researcher shows ACTIVE when research is in progress (no completed_at)');
    console.log('   - Researcher shows IDLE when research is completed or no research exists');
  } else {
    console.log('\n💥 SOME TESTS FAILED! Researcher status detection needs fixing.');
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { simulateResearcherStatus, testActiveWorkflowScenarios };
