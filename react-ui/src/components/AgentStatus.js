import React from 'react';
import { Bot, FileText, Edit3, Search, Upload, Archive, Clock, CheckCircle, AlertCircle } from 'lucide-react';

const AgentStatus = ({ status, workflowProgress, workflowStarting }) => {
  const agents = [
    {
      id: 'newsChief',
      name: 'News Chief',
      icon: Bot,
      description: 'Workflow Coordinator',
      getStatus: () => {
        // Show as active immediately when workflow is starting
        if (workflowStarting) return 'assigning';
        
        if (!status.newsChief?.story) return 'idle';
        const storyStatus = status.newsChief.story.status;
        
        // Map story status to News Chief status
        if (storyStatus === 'assigned') return 'assigning';
        if (storyStatus === 'writing' || storyStatus === 'draft_submitted' || storyStatus === 'under_review' || storyStatus === 'reviewed' || storyStatus === 'needs_revision' || storyStatus === 'revised' || storyStatus === 'publishing') return 'monitoring';
        if (storyStatus === 'published' || storyStatus === 'completed') return 'idle'; // Reset to idle after completion
        
        return storyStatus || 'idle';
      },
      getActivity: () => {
        if (workflowStarting) return 'Assigning story to Reporter';
        if (!status.newsChief?.story) return 'Waiting for assignment';
        const storyStatus = status.newsChief.story.status;
        return getNewsChiefActivity(storyStatus);
      }
    },
    {
      id: 'reporter',
      name: 'Reporter',
      icon: FileText,
      description: 'Article Writer',
      getStatus: () => {
        if (!status.reporter?.assignment) return 'idle';
        const reporterStatus = status.reporter.assignment.reporter_status;
        const waitingStatus = status.reporter.waiting_status;
        
        // Debug logging for Reporter status
        console.log('=== REPORTER STATUS DEBUG ===');
        console.log('Reporter status:', reporterStatus);
        console.log('Reporter waiting_status:', waitingStatus);
        console.log('Reporter assignment:', status.reporter.assignment);
        
        if (waitingStatus && waitingStatus !== 'none') {
          console.log('Reporter waiting status:', waitingStatus);
        }
        
        // Check if waiting for other agents (handle both string and object formats)
        if (typeof waitingStatus === 'string') {
          if (waitingStatus === 'researcher_archivist') return 'waiting';
          if (waitingStatus === 'editor') return 'waiting';
          if (waitingStatus === 'publisher') return 'waiting';
        } else if (typeof waitingStatus === 'object') {
          // Check if any story has waiting status
          const waitingStatuses = Object.values(waitingStatus);
          if (waitingStatuses.includes('researcher_archivist')) return 'waiting';
          if (waitingStatuses.includes('editor')) return 'waiting';
          if (waitingStatuses.includes('publisher')) return 'waiting';
        }
        
        // Special case: if researching but Researcher/Archivist are active, show waiting
        if (reporterStatus === 'researching') {
          const researcherActive = status.researcher?.research_history?.some(session => 
            !session.completed_at && (session.status === 'active' || session.status === 'researching')
          );
          const archivistActive = status.reporter?.archivist_status === 'active';
          if (researcherActive || archivistActive) {
            return 'waiting';
          }
        }
        
        // Check if reporter has completed work - reset to idle after completion
        if (reporterStatus === 'revised' || reporterStatus === 'published' || status.reporter.draft?.status === 'revised') {
          return 'idle';
        }
        return reporterStatus || 'idle';
      },
      getActivity: () => {
        if (!status.reporter?.assignment) return 'Waiting for assignment';
        const reporterStatus = status.reporter.assignment.reporter_status;
        const waitingStatus = status.reporter.waiting_status;
        
        // Check if waiting for other agents (handle both string and object formats)
        if (typeof waitingStatus === 'string') {
          if (waitingStatus === 'researcher_archivist') return 'Waiting for Researcher and Archivist';
          if (waitingStatus === 'editor') {
            console.log('Reporter is waiting for Editor - Editor should be active');
            return 'Waiting for Editor review';
          }
          if (waitingStatus === 'publisher') return 'Waiting for Publisher';
        } else if (typeof waitingStatus === 'object') {
          // Check if any story has waiting status
          const waitingStatuses = Object.values(waitingStatus);
          if (waitingStatuses.includes('researcher_archivist')) return 'Waiting for Researcher and Archivist';
          if (waitingStatuses.includes('editor')) {
            console.log('Reporter is waiting for Editor - Editor should be active');
            return 'Waiting for Editor review';
          }
          if (waitingStatuses.includes('publisher')) return 'Waiting for Publisher';
        }
        
        // Special case: if researching but Researcher/Archivist are active, show waiting
        if (reporterStatus === 'researching') {
          // Check if Researcher is actively working
          const researcherActive = status.researcher?.research_history?.some(session => 
            !session.completed_at && (session.status === 'active' || session.status === 'researching')
          );
          const archivistActive = status.reporter?.archivist_status === 'active';
          
          console.log('Reporter waiting check - researcherActive:', researcherActive);
          console.log('Reporter waiting check - archivistActive:', archivistActive);
          
          if (researcherActive || archivistActive) {
            if (researcherActive && archivistActive) return 'Waiting for Researcher and Archivist';
            if (researcherActive) return 'Waiting for Researcher';
            if (archivistActive) return 'Waiting for Archivist';
          }
        }
        
        if (reporterStatus === 'revised' || status.reporter.draft?.status === 'revised') {
          return 'Article completed and revised';
        }
        return getReporterActivity(reporterStatus);
      }
    },
    {
      id: 'editor',
      name: 'Editor',
      icon: Edit3,
      description: 'Content Reviewer',
      getStatus: () => {
        // Comprehensive debug logging
        console.log('=== EDITOR STATUS DEBUG ===');
        console.log('Editor status object:', status.editor);
        console.log('Reporter status object:', status.reporter);
        console.log('Reporter waiting_status:', status.reporter?.waiting_status);
        
        // Check if there are drafts under review (Editor's own status)
        if (status.editor?.drafts && status.editor.drafts.length > 0) {
          const latestDraft = status.editor.drafts[status.editor.drafts.length - 1];
          console.log('Editor latest draft:', latestDraft);
          console.log('Editor draft review_status:', latestDraft.review_status);
          
          // If draft is being reviewed, show as active
          if (latestDraft.review_status === 'reviewing') {
            console.log('Editor: Draft is being reviewed, returning active');
            return 'active';
          }
          
          // If draft review is completed, show as idle
          if (latestDraft.review_status === 'completed') {
            console.log('Editor: Draft review completed, returning idle');
            return 'idle';
          }
        }
        
        // Check if Reporter is waiting for Editor (fallback indicator)
        const reporterWaiting = status.reporter?.waiting_status === 'editor';
        console.log('Editor status check - reporterWaiting:', reporterWaiting);
        
        // If Reporter is waiting for Editor, show as active
        if (reporterWaiting) {
          console.log('Editor: Reporter is waiting, returning active');
          return 'active';
        }
        
        // Check reviews as fallback
        if (status.editor?.reviews?.length) {
          const latestReview = status.editor.reviews[status.editor.reviews.length - 1];
          console.log('Editor latest review:', latestReview);
          console.log('Editor status check - status:', latestReview.status);
          
          // If review is completed, show as idle
          if (latestReview.status === 'completed') {
            console.log('Editor: Review completed, returning idle');
            return 'idle';
          }
          
          // If review is in progress, show as active
          if (latestReview.status === 'active' || latestReview.status === 'reviewing') {
            console.log('Editor: Review in progress, returning active');
            return 'active';
          }
        }
        
        console.log('Editor: No active work, returning idle');
        return 'idle';
      },
      getActivity: () => {
        if (!status.editor?.reviews?.length) return 'Waiting for draft';
        const reviewCount = status.editor.reviews.length;
        const latestReview = status.editor.reviews[status.editor.reviews.length - 1];
        
        // Check if Reporter is waiting for Editor
        const reporterWaiting = status.reporter?.waiting_status === 'editor';
        
        if (reporterWaiting) {
          return 'Reviewing article content';
        }
        
        if (latestReview.completed_at || latestReview.status === 'completed') {
          return `Completed ${reviewCount} review${reviewCount > 1 ? 's' : ''}`;
        }
        
        return 'Reviewing article content';
      }
    },
    {
      id: 'researcher',
      name: 'Researcher',
      icon: Search,
      description: 'Fact Gatherer',
      getStatus: () => {
        if (!status.researcher?.research_history?.length) return 'idle';
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
      },
      getActivity: () => {
        if (!status.researcher?.research_history?.length) return 'Waiting for research questions';
        const researchCount = status.researcher.research_history.length;
        const latestResearch = status.researcher.research_history[status.researcher.research_history.length - 1];
        if (latestResearch.completed_at) {
          return `Completed ${researchCount} research session${researchCount > 1 ? 's' : ''}`;
        }
        return `Working on research session ${researchCount}`;
      }
    },
    {
      id: 'archivist',
      name: 'Archivist',
      icon: Archive,
      description: 'Historical Search',
      getStatus: () => {
        if (!status.reporter?.archivist_status) return 'idle';
        const archivistStatus = status.reporter.archivist_status;
        
        // Handle object format (story_id -> status mapping)
        if (typeof archivistStatus === 'object') {
          const statuses = Object.values(archivistStatus);
          if (statuses.includes('active')) return 'active';
          if (statuses.includes('completed')) return 'completed';
          if (statuses.includes('error')) return 'error';
          if (statuses.includes('skipped')) return 'completed';
          return 'idle';
        }
        
        // Handle string format (legacy)
        if (archivistStatus === 'completed' || archivistStatus === 'skipped') {
          return 'completed';
        }
        if (archivistStatus === 'active') {
          return 'active';
        }
        if (archivistStatus === 'error') {
          return 'error';
        }
        return 'idle';
      },
      getActivity: () => {
        if (!status.reporter?.archivist_status) return 'Waiting for search request';
        const archivistStatus = status.reporter.archivist_status;
        
        // Handle object format (story_id -> status mapping)
        if (typeof archivistStatus === 'object') {
          const statuses = Object.values(archivistStatus);
          if (statuses.includes('active')) return 'Searching historical articles';
          if (statuses.includes('completed')) return 'Historical search completed';
          if (statuses.includes('error')) return 'Search failed - continuing without history';
          if (statuses.includes('skipped')) return 'Search skipped (not configured)';
          return 'Waiting for search request';
        }
        
        // Handle string format (legacy)
        if (archivistStatus === 'active') {
          return 'Searching historical articles';
        }
        if (archivistStatus === 'completed') {
          return 'Historical search completed';
        }
        if (archivistStatus === 'skipped') {
          return 'Search skipped (not configured)';
        }
        if (archivistStatus === 'error') {
          return 'Search failed - continuing without history';
        }
        return 'Waiting for search request';
      }
    },
    {
      id: 'publisher',
      name: 'Publisher',
      icon: Upload,
      description: 'Article Publisher',
      getStatus: () => {
        // Check if publisher has published this specific story
        if (status.publisher?.publication?.story_id) {
          return 'idle'; // Reset to idle after completion
        }
        if (status.publisher?.total_published > 0) {
          return 'idle'; // Reset to idle after completion
        }
        return 'idle';
      },
      getActivity: () => {
        // Check if publisher has published this specific story
        if (status.publisher?.publication?.story_id) {
          return `Published article to Elasticsearch`;
        }
        if (status.publisher?.total_published > 0) {
          const publishedCount = status.publisher.total_published;
          return `Published ${publishedCount} article${publishedCount > 1 ? 's' : ''}`;
        }
        return 'Waiting for article';
      },
      getArticleLink: () => {
        // Return the story_id if there's a published article
        if (status.publisher?.publication?.story_id) {
          return status.publisher.publication.story_id;
        }
        return null;
      }
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

const getNewsChiefActivity = (storyStatus) => {
  switch (storyStatus) {
    case 'assigned':
      return 'Assigning story to Reporter';
    case 'writing':
      return 'Monitoring Reporter progress';
    case 'draft_submitted':
      return 'Draft submitted for review';
    case 'under_review':
      return 'Article under editorial review';
    case 'reviewed':
      return 'Editor review completed';
    case 'needs_revision':
      return 'Article needs revision';
    case 'revised':
      return 'Article revised by Reporter';
    case 'publishing':
      return 'Publishing article';
    case 'published':
      return 'Article published successfully';
    case 'completed':
      return 'Workflow completed';
    default:
      return 'Managing workflow';
  }
};

const getReporterActivity = (reporterStatus) => {
  switch (reporterStatus) {
    case 'researching':
      return 'Generating outline and research questions';
    case 'writing':
    case 'drafting':
      return 'Writing article with research data';
    case 'draft_complete':
      return 'Draft completed, submitting to Editor';
    case 'editing':
      return 'Applying editorial suggestions';
    case 'published':
      return 'Article published to Elasticsearch';
    default:
      return 'Waiting for assignment';
  }
};

export default AgentStatus;
