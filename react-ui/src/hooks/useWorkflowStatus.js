import { useState, useEffect, useCallback } from 'react';
import newsroomService from '../services/newsroomService';

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
    isComplete: false
  });

  const resetWorkflowProgress = useCallback(() => {
    setWorkflowProgress({
      currentStep: 'idle',
      steps: [],
      isComplete: false
    });
  }, []);

  const [activeStories, setActiveStories] = useState([]);

  const updateStatus = useCallback(async () => {
    setStatus(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      // Always get active stories
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

  useEffect(() => {
    // Initial status check
    updateStatus();

    // Set up polling every 2 seconds
    const interval = setInterval(updateStatus, 2000);

    return () => clearInterval(interval);
  }, [updateStatus]);

  return {
    status,
    workflowProgress,
    activeStories,
    updateStatus,
    resetWorkflowProgress
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
