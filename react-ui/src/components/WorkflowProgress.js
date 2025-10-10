import React from 'react';
import { CheckCircle, Clock, AlertCircle, Loader } from 'lucide-react';

const WorkflowProgress = ({ workflowProgress, status }) => {
  const getStepIcon = (stepStatus) => {
    switch (stepStatus) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-success-600" />;
      case 'active':
        return <Loader className="h-5 w-5 text-primary-600 animate-spin" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-gray-400" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-error-600" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStepStatusClass = (stepStatus) => {
    switch (stepStatus) {
      case 'completed':
        return 'text-success-600 bg-success-50 border-success-200';
      case 'active':
        return 'text-primary-600 bg-primary-50 border-primary-200';
      case 'error':
        return 'text-error-600 bg-error-50 border-error-200';
      default:
        return 'text-gray-500 bg-gray-50 border-gray-200';
    }
  };

  if (!workflowProgress.steps.length) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow Progress</h3>
        <div className="text-center text-gray-500 py-8">
          <Clock className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No workflow started yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Workflow Progress</h3>
        {workflowProgress.isComplete && (
          <span className="status-badge status-completed">
            <CheckCircle className="h-4 w-4 mr-1" />
            Complete
          </span>
        )}
      </div>

      <div className="space-y-4">
        {workflowProgress.steps.map((step, index) => (
          <div
            key={step.id}
            className={`flex items-center p-4 rounded-lg border-2 transition-all duration-300 ${getStepStatusClass(step.status)}`}
          >
            <div className="flex-shrink-0 mr-4">
              {getStepIcon(step.status)}
            </div>
            <div className="flex-grow">
              <h4 className="font-medium">{step.name}</h4>
              {step.status === 'active' && (
                <p className="text-sm opacity-75 mt-1">
                  {getActiveStepDescription(step.id, status)}
                </p>
              )}
            </div>
            {step.status === 'completed' && (
              <div className="flex-shrink-0">
                <span className="text-sm font-medium">✓</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {workflowProgress.isComplete && (
        <div className="mt-6 p-4 bg-success-50 border border-success-200 rounded-lg">
          <div className="flex items-center">
            <CheckCircle className="h-5 w-5 text-success-600 mr-2" />
            <span className="text-success-800 font-medium">
              Article workflow completed successfully!
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

const getActiveStepDescription = (stepId, status) => {
  switch (stepId) {
    case 'researching':
      return 'Gathering facts and generating research questions...';
    case 'writing':
      return 'Writing article with research data...';
    case 'reviewing':
      return 'Editor is reviewing content for quality...';
    case 'revising':
      return 'Applying editorial feedback...';
    case 'publishing':
      return 'Publishing article to Elasticsearch...';
    default:
      return 'Processing...';
  }
};

export default WorkflowProgress;
