import React from 'react';
import { Bot, FileText, Edit3, Search, Upload, Archive, Clock, CheckCircle, AlertCircle } from 'lucide-react';

const AgentStatus = ({ status, workflowProgress, workflowStarting }) => {
  // Derive agent status from workflow progress (event-driven)
  const getAgentStatusFromWorkflow = (agentId) => {
    const currentStep = workflowProgress.currentStep;
    const isComplete = workflowProgress.isComplete;

    // If workflow is complete, all agents are idle
    if (isComplete) {
      return { status: 'idle', activity: 'Workflow completed' };
    }

    // Map workflow steps to agent activity
    switch (agentId) {
      case 'newsChief':
        if (workflowStarting) return { status: 'active', activity: 'Assigning story to Reporter' };
        if (currentStep === 'idle') return { status: 'idle', activity: 'Waiting for assignment' };
        return { status: 'active', activity: 'Monitoring workflow' };

      case 'reporter':
        if (currentStep === 'assigned') return { status: 'active', activity: 'Accepting assignment' };
        if (currentStep === 'researching') return { status: 'waiting', activity: 'Waiting for research data' };
        if (currentStep === 'writing') return { status: 'active', activity: 'Writing article' };
        if (currentStep === 'reviewing') return { status: 'waiting', activity: 'Waiting for Editor review' };
        if (currentStep === 'revising') return { status: 'active', activity: 'Applying editorial feedback' };
        if (currentStep === 'publishing') return { status: 'waiting', activity: 'Waiting for Publisher' };
        return { status: 'idle', activity: 'Waiting for assignment' };

      case 'editor':
        if (currentStep === 'reviewing') return { status: 'active', activity: 'Reviewing article content' };
        if (currentStep === 'revising') return { status: 'idle', activity: 'Review completed' };
        return { status: 'idle', activity: 'Waiting for draft' };

      case 'researcher':
        if (currentStep === 'researching') return { status: 'active', activity: 'Researching facts and data' };
        if (currentStep === 'writing' || currentStep === 'reviewing' || currentStep === 'revising') {
          return { status: 'idle', activity: 'Research completed' };
        }
        return { status: 'idle', activity: 'Waiting for research questions' };

      case 'archivist':
        if (currentStep === 'researching') return { status: 'active', activity: 'Searching historical articles' };
        if (currentStep === 'writing' || currentStep === 'reviewing' || currentStep === 'revising') {
          return { status: 'idle', activity: 'Historical search completed' };
        }
        return { status: 'idle', activity: 'Waiting for search request' };

      case 'publisher':
        if (currentStep === 'publishing') return { status: 'active', activity: 'Publishing to Elasticsearch' };
        return { status: 'idle', activity: 'Waiting for article' };

      default:
        return { status: 'idle', activity: 'Idle' };
    }
  };

  const agents = [
    {
      id: 'newsChief',
      name: 'News Chief',
      icon: Bot,
      description: 'Workflow Coordinator',
      getStatus: () => getAgentStatusFromWorkflow('newsChief').status,
      getActivity: () => getAgentStatusFromWorkflow('newsChief').activity
    },
    {
      id: 'reporter',
      name: 'Reporter',
      icon: FileText,
      description: 'Article Writer',
      getStatus: () => getAgentStatusFromWorkflow('reporter').status,
      getActivity: () => getAgentStatusFromWorkflow('reporter').activity
    },
    {
      id: 'editor',
      name: 'Editor',
      icon: Edit3,
      description: 'Content Reviewer',
      getStatus: () => getAgentStatusFromWorkflow('editor').status,
      getActivity: () => getAgentStatusFromWorkflow('editor').activity
    },
    {
      id: 'researcher',
      name: 'Researcher',
      icon: Search,
      description: 'Fact Gatherer',
      getStatus: () => getAgentStatusFromWorkflow('researcher').status,
      getActivity: () => getAgentStatusFromWorkflow('researcher').activity
    },
    {
      id: 'archivist',
      name: 'Archivist',
      icon: Archive,
      description: 'Historical Search',
      getStatus: () => getAgentStatusFromWorkflow('archivist').status,
      getActivity: () => getAgentStatusFromWorkflow('archivist').activity
    },
    {
      id: 'publisher',
      name: 'Publisher',
      icon: Upload,
      description: 'Article Publisher',
      getStatus: () => getAgentStatusFromWorkflow('publisher').status,
      getActivity: () => getAgentStatusFromWorkflow('publisher').activity,
      getArticleLink: () => workflowProgress.story_id && workflowProgress.isComplete ? workflowProgress.story_id : null
    }
  ];

  const getStatusIcon = (agentStatus) => {
    switch (agentStatus) {
      case 'active':
      case 'researching':
      case 'writing':
      case 'drafting':
      case 'editing':
      case 'reviewing':
      case 'publishing':
      case 'revised':
      case 'assigning':
      case 'monitoring':
        return <div className="relative">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <div className="absolute inset-0 w-3 h-3 bg-green-500 rounded-full animate-ping opacity-75"></div>
        </div>;
      case 'completed':
      case 'published':
      case 'draft_complete':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'error':
        return <div className="relative">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
          <div className="absolute inset-0 w-3 h-3 bg-red-500 rounded-full animate-ping opacity-75"></div>
        </div>;
      case 'waiting':
        return <div className="relative">
          <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></div>
          <div className="absolute inset-0 w-3 h-3 bg-yellow-500 rounded-full animate-ping opacity-75"></div>
        </div>;
      default:
        return <div className="w-3 h-3 bg-blue-500 rounded-full"></div>;
    }
  };

  const getStatusClass = (agentStatus) => {
    switch (agentStatus) {
      case 'active':
      case 'researching':
      case 'writing':
      case 'drafting':
      case 'editing':
      case 'reviewing':
      case 'publishing':
      case 'revised':
      case 'assigning':
      case 'monitoring':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'completed':
      case 'published':
      case 'draft_complete':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'waiting':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Agent Status</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => {
          const Icon = agent.icon;
          const agentStatus = agent.getStatus();
          const activity = agent.getActivity();
          
          return (
            <div
              key={agent.id}
              className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                agentStatus === 'idle' 
                  ? 'bg-blue-50 border-blue-200' 
                  : agentStatus === 'completed'
                  ? 'bg-green-50 border-green-200'
                  : agentStatus === 'active' || agentStatus.includes('ing') || agentStatus.includes('ed') || agentStatus === 'revised' || agentStatus === 'assigning' || agentStatus === 'monitoring'
                  ? 'bg-green-50 border-green-200'
                  : agentStatus === 'waiting'
                  ? 'bg-yellow-50 border-yellow-200'
                  : agentStatus === 'error'
                  ? 'bg-red-50 border-red-200'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center">
                  <Icon className="h-5 w-5 text-gray-600 mr-2" />
                  <div>
                    <h4 className="font-medium text-gray-900">{agent.name}</h4>
                    <p className="text-sm text-gray-500">{agent.description}</p>
                  </div>
                </div>
                <div className="flex items-center">
                  {getStatusIcon(agentStatus)}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Status:</span>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusClass(agentStatus)}`}>
                    {agentStatus}
                  </span>
                </div>
                
                <div>
                  <span className="text-sm font-medium text-gray-700">Activity:</span>
                  <p className="text-sm text-gray-600 mt-1">{activity}</p>
                  {agent.id === 'publisher' && agent.getArticleLink && agent.getArticleLink() && (
                    <div className="mt-3">
                      <button
                        onClick={() => {
                          window.history.pushState({}, '', `/article/${agent.getArticleLink()}`);
                          window.dispatchEvent(new PopStateEvent('popstate'));
                        }}
                        className="inline-flex items-center px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
                      >
                        📄 View Article
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AgentStatus;
