import { useState, useEffect, useCallback, useRef } from 'react';
import newsroomService from '../services/newsroomService';
import eventHubClient from '../services/eventHubClient';

export const useWorkflowStatus = (storyId, isActive) => {
  const [status, setStatus] = useState({
    newsChief: null,
    reporter: null,
    editor: null,
    researcher: null,
    publisher: null,
    isLoading: false,
    error: null
  });

  const [workflowProgress, setWorkflowProgress] = useState({
    currentStep: 'idle',
    steps: [],
    isComplete: false,
    story_id: storyId
  });

  const [activeStories, setActiveStories] = useState([]);
  const [realtimeEvents, setRealtimeEvents] = useState([]);
  const eventListenersRef = useRef([]);

  const resetWorkflowProgress = useCallback(() => {
    setWorkflowProgress({
      currentStep: 'idle',
      steps: [],
      isComplete: false,
      story_id: null
    });
  }, []);

  // Initial status fetch (one-time, no polling)
  const fetchInitialStatus = useCallback(async () => {
    setStatus(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      // Get active stories
      const activeStoriesData = await newsroomService.getActiveStories();
      setActiveStories(activeStoriesData.active_stories || []);

      // If we have a specific story ID and it's active, get detailed status
      if (storyId && isActive) {
        const agentStatus = await newsroomService.getAllAgentStatus(storyId);
        setStatus(prev => ({ ...prev, ...agentStatus, isLoading: false }));

        // Update workflow progress based on agent status
        const progress = determineWorkflowProgress(agentStatus);
        setWorkflowProgress(progress);
      } else {
        // Just get basic agent status without specific story
        const basicStatus = await newsroomService.getAllAgentStatus(null);
        setStatus(prev => ({ ...prev, ...basicStatus, isLoading: false }));
      }

    } catch (error) {
      setStatus(prev => ({
        ...prev,
        isLoading: false,
        error: error.message
      }));
    }
  }, [storyId, isActive]);

  // Handle real-time events from Event Hub
  const handleRealtimeEvent = useCallback((event) => {
    console.log('📨 Real-time event received:', event);

    // Add to events list
    setRealtimeEvents(prev => [...prev.slice(-50), event]); // Keep last 50 events

    // Update workflow progress based on event type
    const eventType = event.event_type;
    const eventStoryId = event.story_id;

    // Only process events for our current story (or if no story filter)
    if (!storyId || eventStoryId === storyId) {
      setWorkflowProgress(prev => {
        const newProgress = { ...prev, story_id: eventStoryId };

        // Map events to workflow steps
        switch (eventType) {
          case 'story_assigned':
            newProgress.currentStep = 'assigned';
            newProgress.steps = [
              { id: 'assigned', name: 'Story Assigned', status: 'completed' }
            ];
            break;

          case 'research_started':
            newProgress.currentStep = 'researching';
            if (!newProgress.steps.find(s => s.id === 'researching')) {
              newProgress.steps.push({
                id: 'researching',
                name: 'Research & Planning',
                status: 'active'
              });
            }
            break;

          case 'research_completed':
            const researchStep = newProgress.steps.find(s => s.id === 'researching');
            if (researchStep) {
              researchStep.status = 'completed';
            }
            newProgress.currentStep = 'writing';
            break;

          case 'article_writing_started':
            newProgress.currentStep = 'writing';
            if (!newProgress.steps.find(s => s.id === 'writing')) {
              newProgress.steps.push({
                id: 'writing',
                name: 'Writing Article',
                status: 'active'
              });
            }
            break;

          case 'article_drafted':
            const writingStep = newProgress.steps.find(s => s.id === 'writing');
            if (writingStep) {
              writingStep.status = 'completed';
            }
            newProgress.currentStep = 'reviewing';
            break;

          case 'review_started':
            newProgress.currentStep = 'reviewing';
            if (!newProgress.steps.find(s => s.id === 'reviewing')) {
              newProgress.steps.push({
                id: 'reviewing',
                name: 'Editorial Review',
                status: 'active'
              });
            }
            break;

          case 'review_completed':
            const reviewStep = newProgress.steps.find(s => s.id === 'reviewing');
            if (reviewStep) {
              reviewStep.status = 'completed';
            }
            newProgress.currentStep = 'revising';
            break;

          case 'edits_applied':
            const revisingStep = newProgress.steps.find(s => s.id === 'revising');
            if (revisingStep) {
              revisingStep.status = 'completed';
            }
            newProgress.currentStep = 'publishing';
            break;

          case 'publication_started':
            newProgress.currentStep = 'publishing';
            if (!newProgress.steps.find(s => s.id === 'publishing')) {
              newProgress.steps.push({
                id: 'publishing',
                name: 'Publishing Article',
                status: 'active'
              });
            }
            break;

          case 'publication_completed':
            const publishingStep = newProgress.steps.find(s => s.id === 'publishing');
            if (publishingStep) {
              publishingStep.status = 'completed';
            }
            newProgress.currentStep = 'completed';
            newProgress.isComplete = true;
            break;
        }

        return newProgress;
      });
    }

    // Optionally refresh status after certain events
    if (['publication_completed', 'story_assigned'].includes(eventType)) {
      fetchInitialStatus();
    }
  }, [storyId, fetchInitialStatus]);

  // Connect to Event Hub on mount
  useEffect(() => {
    console.log('🔌 Connecting to Event Hub...');

    // Connect to Event Hub (with story filter if available)
    eventHubClient.connect(storyId);

    // Subscribe to all events
    const unsubscribe = eventHubClient.on('*', handleRealtimeEvent);
    eventListenersRef.current.push(unsubscribe);

    // Subscribe to connection events
    const unsubscribeConnected = eventHubClient.on('connected', () => {
      console.log('✅ Event Hub connected');
      // Fetch initial status when connected
      fetchInitialStatus();
    });
    eventListenersRef.current.push(unsubscribeConnected);

    const unsubscribeError = eventHubClient.on('error', (error) => {
      console.error('❌ Event Hub error:', error);
      setStatus(prev => ({ ...prev, error: 'Event Hub connection error' }));
    });
    eventListenersRef.current.push(unsubscribeError);

    // Fetch initial status
    fetchInitialStatus();

    // Cleanup on unmount
    return () => {
      console.log('🔌 Disconnecting from Event Hub...');
      eventListenersRef.current.forEach(unsub => unsub());
      eventListenersRef.current = [];
      eventHubClient.disconnect();
    };
  }, [storyId, handleRealtimeEvent, fetchInitialStatus]);

  return {
    status,
    workflowProgress,
    activeStories,
    realtimeEvents,
    updateStatus: fetchInitialStatus, // Manual refresh if needed
    resetWorkflowProgress,
    isConnectedToEventHub: eventHubClient.isConnectedToEventHub()
  };
};

const determineWorkflowProgress = (agentStatus) => {
  const steps = [];
  let currentStep = 'idle';
  let isComplete = false;

  // News Chief story status
  if (agentStatus.newsChief?.story) {
    const storyStatus = agentStatus.newsChief.story.status;

    switch (storyStatus) {
      case 'assigned':
        steps.push({ id: 'assigned', name: 'Story Assigned', status: 'completed' });
        currentStep = 'researching';
        break;
      case 'writing':
        steps.push({ id: 'assigned', name: 'Story Assigned', status: 'completed' });
        steps.push({ id: 'researching', name: 'Research & Planning', status: 'completed' });
        currentStep = 'writing';
        break;
      case 'draft_submitted':
        steps.push({ id: 'assigned', name: 'Story Assigned', status: 'completed' });
        steps.push({ id: 'researching', name: 'Research & Planning', status: 'completed' });
        steps.push({ id: 'writing', name: 'Writing Article', status: 'completed' });
        currentStep = 'reviewing';
        break;
      case 'under_review':
        steps.push({ id: 'assigned', name: 'Story Assigned', status: 'completed' });
        steps.push({ id: 'researching', name: 'Research & Planning', status: 'completed' });
        steps.push({ id: 'writing', name: 'Writing Article', status: 'completed' });
        steps.push({ id: 'reviewing', name: 'Editorial Review', status: 'active' });
        currentStep = 'reviewing';
        break;
      case 'reviewed':
        steps.push({ id: 'assigned', name: 'Story Assigned', status: 'completed' });
        steps.push({ id: 'researching', name: 'Research & Planning', status: 'completed' });
        steps.push({ id: 'writing', name: 'Writing Article', status: 'completed' });
        steps.push({ id: 'reviewing', name: 'Editorial Review', status: 'completed' });
        currentStep = 'revising';
        break;
      case 'needs_revision':
        steps.push({ id: 'assigned', name: 'Story Assigned', status: 'completed' });
        steps.push({ id: 'researching', name: 'Research & Planning', status: 'completed' });
        steps.push({ id: 'writing', name: 'Writing Article', status: 'completed' });
        steps.push({ id: 'reviewing', name: 'Editorial Review', status: 'completed' });
        steps.push({ id: 'revising', name: 'Applying Edits', status: 'active' });
        currentStep = 'revising';
        break;
      case 'revised':
        steps.push({ id: 'assigned', name: 'Story Assigned', status: 'completed' });
        steps.push({ id: 'researching', name: 'Research & Planning', status: 'completed' });
        steps.push({ id: 'writing', name: 'Writing Article', status: 'completed' });
        steps.push({ id: 'reviewing', name: 'Editorial Review', status: 'completed' });
        steps.push({ id: 'revising', name: 'Applying Edits', status: 'completed' });
        currentStep = 'publishing';
        break;
      case 'publishing':
        steps.push({ id: 'assigned', name: 'Story Assigned', status: 'completed' });
        steps.push({ id: 'researching', name: 'Research & Planning', status: 'completed' });
        steps.push({ id: 'writing', name: 'Writing Article', status: 'completed' });
        steps.push({ id: 'reviewing', name: 'Editorial Review', status: 'completed' });
        steps.push({ id: 'revising', name: 'Applying Edits', status: 'completed' });
        steps.push({ id: 'publishing', name: 'Publishing Article', status: 'active' });
        currentStep = 'publishing';
        break;
      case 'published':
        steps.push({ id: 'assigned', name: 'Story Assigned', status: 'completed' });
        steps.push({ id: 'researching', name: 'Research & Planning', status: 'completed' });
        steps.push({ id: 'writing', name: 'Writing Article', status: 'completed' });
        steps.push({ id: 'reviewing', name: 'Editorial Review', status: 'completed' });
        steps.push({ id: 'revising', name: 'Applying Edits', status: 'completed' });
        steps.push({ id: 'publishing', name: 'Publishing Article', status: 'completed' });
        currentStep = 'completed';
        isComplete = true;
        break;
      case 'completed':
        steps.push({ id: 'assigned', name: 'Story Assigned', status: 'completed' });
        steps.push({ id: 'researching', name: 'Research & Planning', status: 'completed' });
        steps.push({ id: 'writing', name: 'Writing Article', status: 'completed' });
        steps.push({ id: 'reviewing', name: 'Editorial Review', status: 'completed' });
        steps.push({ id: 'revising', name: 'Applying Edits', status: 'completed' });
        steps.push({ id: 'publishing', name: 'Publishing Article', status: 'completed' });
        currentStep = 'completed';
        isComplete = true;
        break;
    }
  }

  // Add current step if not already added
  if (currentStep !== 'idle' && currentStep !== 'completed') {
    const stepNames = {
      'researching': 'Research & Planning',
      'writing': 'Writing Article',
      'reviewing': 'Editorial Review',
      'revising': 'Applying Edits',
      'publishing': 'Publishing Article'
    };

    if (!steps.find(step => step.id === currentStep)) {
      steps.push({
        id: currentStep,
        name: stepNames[currentStep] || currentStep,
        status: 'active'
      });
    }
  }

  return {
    currentStep,
    steps,
    isComplete
  };
};
