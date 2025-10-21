import React, { useState, useEffect } from 'react';
import { Newspaper, AlertCircle } from 'lucide-react';
import WorkflowForm from './components/WorkflowForm';
import WorkflowProgress from './components/WorkflowProgress';
import AgentStatus from './components/AgentStatus';
import ArticleViewer from './components/ArticleViewer';
import { useWorkflowStatus } from './hooks/useWorkflowStatus';
import newsroomService from './services/newsroomService';

function App() {
  const [currentStory, setCurrentStory] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [workflowStarting, setWorkflowStarting] = useState(false);
  const [error, setError] = useState(null);
  const [viewingArticle, setViewingArticle] = useState(null);
  const [storyRestored, setStoryRestored] = useState(false);
  const [articleHeadline, setArticleHeadline] = useState(null);

  const { status, workflowProgress, activeStories, updateStatus, resetWorkflowProgress } = useWorkflowStatus(
    currentStory?.story_id,
    !!currentStory
  );

  // Handle routing for article viewer
  useEffect(() => {
    const handleRouteChange = () => {
      const path = window.location.pathname;
      console.log('Route change detected - path:', path);

      if (path.startsWith('/article/')) {
        const storyId = path.split('/article/')[1];
        console.log('Setting viewingArticle to:', storyId);
        setViewingArticle(storyId);
      } else {
        console.log('Clearing viewingArticle');
        setViewingArticle(null);
      }
    };

    // Check initial route
    handleRouteChange();

    // Listen for route changes
    window.addEventListener('popstate', handleRouteChange);
    return () => window.removeEventListener('popstate', handleRouteChange);
  }, []);

  // Restore current story from localStorage on page load
  useEffect(() => {
    const savedStory = localStorage.getItem('currentStory');
    if (savedStory) {
      try {
        const storyData = JSON.parse(savedStory);
        setCurrentStory(storyData);
        setStoryRestored(true);
        // Clear the restored flag after a few seconds
        setTimeout(() => setStoryRestored(false), 5000);
      } catch (error) {
        console.error('Error parsing saved story:', error);
        localStorage.removeItem('currentStory');
      }
    }
  }, []);

  // Check if current story is still active when activeStories updates
  useEffect(() => {
    if (currentStory && activeStories && activeStories.length > 0) {
      const isStillActive = activeStories.some(story => story.story_id === currentStory.story_id);
      if (!isStillActive) {
        // Story is no longer active, clear it
        console.log('Current story is no longer active, clearing...');
        setCurrentStory(null);
      }
    }
  }, [activeStories, currentStory]);

  // Save current story to localStorage whenever it changes
  useEffect(() => {
    if (currentStory) {
      localStorage.setItem('currentStory', JSON.stringify(currentStory));
    } else {
      localStorage.removeItem('currentStory');
    }
  }, [currentStory]);

  // Fetch article headline when workflow is complete
  useEffect(() => {
    const fetchHeadline = async () => {
      if (workflowProgress.isComplete && currentStory?.story_id && !articleHeadline) {
        try {
          const response = await fetch(`http://localhost:8085/article/${currentStory.story_id}`);
          if (response.ok) {
            const articleData = await response.json();
            // Extract headline from content if it starts with "HEADLINE:"
            let headline = articleData.headline;
            if (headline === 'Untitled' && articleData.content) {
              const lines = articleData.content.split('\n');
              const headlineLine = lines.find(line => line.trim().startsWith('HEADLINE:'));
              if (headlineLine) {
                headline = headlineLine.replace('HEADLINE:', '').trim();
              }
            }
            setArticleHeadline(headline);
          }
        } catch (error) {
          console.error('Error fetching article headline:', error);
        }
      }
    };

    fetchHeadline();
  }, [workflowProgress.isComplete, currentStory, articleHeadline]);

  const handleStartWorkflow = async (storyData) => {
    setIsLoading(true);
    setWorkflowStarting(true);
    setError(null);
    setCurrentStory(null);
    setArticleHeadline(null);

    // Reset workflow progress for new story
    resetWorkflowProgress();

    try {
      const response = await newsroomService.assignStory(storyData);
      
      if (response.status === 'success') {
        setCurrentStory({
          story_id: response.story_id,
          ...storyData
        });
      } else {
        throw new Error(response.message || 'Failed to start workflow');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
      setWorkflowStarting(false);
    }
  };

  const handleReset = async () => {
    try {
      // Clear all agent states
      await newsroomService.clearAllAgents();

      // Clear local state
      setCurrentStory(null);
      setError(null);
      setStoryRestored(false);
      setWorkflowStarting(false);
      setArticleHeadline(null);

      // Reset workflow progress
      resetWorkflowProgress();

      // Clear localStorage
      localStorage.removeItem('currentStory');

      console.log('✅ All agents cleared and reset to idle state');
    } catch (error) {
      console.error('Error clearing agents:', error);
      setError('Failed to clear all agents: ' + error.message);
    }
  };

  const handleBackToDashboard = () => {
    setViewingArticle(null);
    window.history.pushState({}, '', '/');
  };

  // Show article viewer if viewing an article
  if (viewingArticle) {
    return <ArticleViewer storyId={viewingArticle} onBack={handleBackToDashboard} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Newspaper className="h-8 w-8 text-primary-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">Elastic News</h1>
            </div>
            <div className="text-sm text-gray-500">
              Multi-Agent Newsroom Workflow
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-error-50 border border-error-200 rounded-lg">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-error-600 mr-2" />
              <span className="text-error-800 font-medium">Error: {error}</span>
            </div>
          </div>
        )}

        {storyRestored && currentStory && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center">
              <Newspaper className="h-5 w-5 text-blue-600 mr-2" />
              <span className="text-blue-800 font-medium">
                Continuing to monitor story: "{articleHeadline || currentStory.topic}" (ID: {currentStory.story_id})
              </span>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Form and Progress */}
          <div className="space-y-6">
            <WorkflowForm
              onSubmit={handleStartWorkflow}
              isLoading={isLoading}
            />
            
            <WorkflowProgress 
              workflowProgress={workflowProgress}
              status={status}
            />
          </div>

          {/* Right Column - Agent Status */}
          <div>
            <AgentStatus 
              status={status}
              workflowProgress={workflowProgress}
              workflowStarting={workflowStarting}
            />
          </div>
        </div>

        {/* Active Stories */}
        {activeStories.length > 0 && (
          <div className="mt-8 card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Stories</h3>
            <div className="space-y-3">
              {activeStories.map((story, index) => (
                <div key={story.story_id || index} className="p-4 bg-gray-50 rounded-lg border">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">{story.topic}</h4>
                      <p className="text-sm text-gray-600">{story.angle}</p>
                      <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                        <span>Status: <span className="font-medium">{story.status}</span></span>
                        <span>Words: <span className="font-medium">{story.target_length}</span></span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">ID: {story.story_id}</p>
                      <p className="text-xs text-gray-400">
                        {new Date(story.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Current Story Info */}
        {currentStory && (
          <div className="mt-8 card">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Current Story</h3>
                <div className="mt-2 space-y-1">
                  <p><span className="font-medium">Topic:</span> {currentStory.topic}</p>
                  <p><span className="font-medium">Angle:</span> {currentStory.angle}</p>
                  <p><span className="font-medium">Target Length:</span> {currentStory.target_length} words</p>
                  <p><span className="font-medium">Story ID:</span> {currentStory.story_id}</p>
                </div>
              </div>
              <div className="flex flex-col gap-2">
                <button
                  onClick={handleReset}
                  className="btn-primary px-4 py-2 text-sm font-medium"
                >
                  🆕 Start New Story
                </button>
                <button
                  onClick={handleReset}
                  className="btn-secondary px-4 py-2 text-sm font-medium"
                >
                  Reset All
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Start New Story Button - Always visible */}
        {!currentStory && (
          <div className="mt-8 card">
            <div className="text-center">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Ready to Create Another Article?</h3>
              <p className="text-gray-600 mb-4">All agents are idle and ready for a new story assignment.</p>
              <button
                onClick={handleReset}
                className="btn-primary px-6 py-3 text-base font-medium"
              >
                🆕 Start New Story
              </button>
            </div>
          </div>
        )}

        {/* Debug Info */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-8 card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Debug Info</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Workflow Status</h4>
                <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto">
                  {JSON.stringify(workflowProgress, null, 2)}
                </pre>
              </div>
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Agent Status</h4>
                <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto">
                  {JSON.stringify(status, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
