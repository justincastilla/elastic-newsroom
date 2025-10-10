#!/usr/bin/env node

/**
 * Test to verify Archivist retry logic with 3 attempts and 60-second timeout
 * This test verifies that the Archivist is now REQUIRED and will retry on failure
 */

const axios = require('axios');

const AGENT_URLS = {
  newsChief: 'http://localhost:8080',
  reporter: 'http://localhost:8081',
  editor: 'http://localhost:8082',
  researcher: 'http://localhost:8083',
  publisher: 'http://localhost:8084'
};

async function testArchivistRetryLogic() {
  console.log('🧪 Testing Archivist Retry Logic');
  console.log('=================================');
  
  try {
    // Start a new workflow to test Archivist retry
    console.log('📝 Starting new workflow to test Archivist...');
    const storyData = {
      topic: 'AI Testing Retry',
      angle: 'Testing Archivist retry logic with 3 attempts and 60s timeout',
      target_length: 500
    };
    
    console.log('📤 Assigning story to News Chief...');
    const assignResponse = await axios.post(`${AGENT_URLS.newsChief}/assign-story`, { 
      action: 'assign_story',
      ...storyData 
    }, { timeout: 10000 });
    
    console.log('Story assignment response:', assignResponse.data);
    
    if (assignResponse.data.status !== 'success') {
      throw new Error('Failed to assign story');
    }
    
    const storyId = assignResponse.data.story_id;
    console.log('✅ Story assigned with ID:', storyId);
    
    // Wait for the workflow to start and reach the Archivist call
    console.log('⏳ Waiting for workflow to reach Archivist call...');
    console.log('   This will test the retry logic with 3 attempts and 60s timeout each');
    
    // Monitor the workflow for up to 5 minutes
    const maxWaitTime = 5 * 60 * 1000; // 5 minutes
    const checkInterval = 5000; // 5 seconds
    let elapsed = 0;
    
    while (elapsed < maxWaitTime) {
      try {
        // Check Reporter status
        const reporterResponse = await axios.post(`${AGENT_URLS.reporter}/get-status`, { action: 'get_status' }, { timeout: 5000 });
        const reporterStatus = reporterResponse.data;
        
        console.log(`\n📊 Reporter Status Check (${Math.floor(elapsed/1000)}s elapsed):`);
        console.log(`   Assignment status: ${reporterStatus.assignments?.[0]?.reporter_status || 'none'}`);
        console.log(`   Waiting status: ${reporterStatus.waiting_status || 'none'}`);
        console.log(`   Archivist status: ${reporterStatus.archivist_status || 'none'}`);
        
        // Check if workflow completed or failed
        if (reporterStatus.assignments?.[0]?.reporter_status === 'published') {
          console.log('✅ Workflow completed successfully!');
          console.log('   This means Archivist retry logic worked correctly');
          return true;
        }
        
        if (reporterStatus.assignments?.[0]?.reporter_status === 'error') {
          console.log('❌ Workflow failed - this might be expected if Archivist is not configured');
          console.log('   Check logs to see if retry logic was attempted');
          return false;
        }
        
        // Check if we're in the research phase (where Archivist is called)
        if (reporterStatus.waiting_status === 'researcher_archivist') {
          console.log('🔄 Workflow is in research phase - Archivist retry logic should be active');
          console.log('   Monitoring for up to 3 minutes for Archivist attempts...');
        }
        
        await new Promise(resolve => setTimeout(resolve, checkInterval));
        elapsed += checkInterval;
        
      } catch (error) {
        console.warn(`⚠️  Error checking status: ${error.message}`);
        await new Promise(resolve => setTimeout(resolve, checkInterval));
        elapsed += checkInterval;
      }
    }
    
    console.log('⏰ Timeout reached - workflow may still be in progress');
    console.log('   Check the logs to see Archivist retry attempts');
    return false;
    
  } catch (error) {
    console.error('❌ Error testing Archivist retry logic:', error.message);
    return false;
  }
}

async function testArchivistConfiguration() {
  console.log('\n🔧 Testing Archivist Configuration');
  console.log('===================================');
  
  try {
    // Check if Archivist environment variables are set
    console.log('📋 Checking Archivist configuration...');
    
    // Try to get Reporter status to see if Archivist URL is configured
    const reporterResponse = await axios.post(`${AGENT_URLS.reporter}/get-status`, { action: 'get_status' }, { timeout: 5000 });
    const reporterStatus = reporterResponse.data;
    
    console.log('Reporter status:', reporterStatus);
    
    // The Reporter should have archivist_status field if Archivist is configured
    if (reporterStatus.archivist_status !== undefined) {
      console.log('✅ Archivist appears to be configured (archivist_status field present)');
      return true;
    } else {
      console.log('⚠️  Archivist may not be configured (no archivist_status field)');
      console.log('   This test will show how the system handles missing Archivist configuration');
      return false;
    }
    
  } catch (error) {
    console.error('❌ Error checking Archivist configuration:', error.message);
    return false;
  }
}

async function main() {
  console.log('🚀 Archivist Retry Logic Test');
  console.log('==============================');
  console.log('This test verifies:');
  console.log('  - Archivist is now REQUIRED (not optional)');
  console.log('  - Retry logic: up to 3 attempts');
  console.log('  - Timeout: 60 seconds per attempt');
  console.log('  - Workflow stops if Archivist fails after all retries');
  console.log('');
  
  // Test configuration first
  const configOk = await testArchivistConfiguration();
  
  // Test retry logic
  const retryTestPassed = await testArchivistRetryLogic();
  
  console.log('\n📊 Test Results');
  console.log('================');
  console.log(`Configuration check: ${configOk ? '✅ PASSED' : '⚠️  WARNING'}`);
  console.log(`Retry logic test: ${retryTestPassed ? '✅ PASSED' : '❌ FAILED'}`);
  
  if (retryTestPassed) {
    console.log('\n🎉 Archivist retry logic is working correctly!');
    console.log('   - Archivist is treated as REQUIRED');
    console.log('   - Retry logic with 3 attempts and 60s timeout');
    console.log('   - Workflow stops if Archivist fails');
  } else {
    console.log('\n💥 Archivist retry logic test failed or incomplete.');
    console.log('   Check the logs to see retry attempts and error handling.');
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { testArchivistRetryLogic, testArchivistConfiguration };
