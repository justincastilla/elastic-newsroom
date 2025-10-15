import React, { useState } from 'react';
import { Send, FileText, Target, Hash } from 'lucide-react';

const WorkflowForm = ({ onSubmit, isLoading }) => {
  const [formData, setFormData] = useState({
    topic: '',
    angle: '',
    target_length: 1200
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'target_length' ? parseInt(value) || 0 : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.topic.trim() && formData.angle.trim()) {
      onSubmit(formData);
    }
  };

  return (
    <div className="card">
      <div className="flex items-center mb-6">
        <FileText className="h-6 w-6 text-primary-600 mr-3" />
        <h2 className="text-2xl font-bold text-gray-900">Create News Article</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-2">
            <Target className="h-4 w-4 inline mr-1" />
            Topic
          </label>
          <input
            type="text"
            id="topic"
            name="topic"
            value={formData.topic}
            onChange={handleChange}
            placeholder="e.g., AI Agents Transform Modern Newsrooms"
            className="input-field"
            required
            disabled={isLoading}
          />
        </div>

        <div>
          <label htmlFor="angle" className="block text-sm font-medium text-gray-700 mb-2">
            <FileText className="h-4 w-4 inline mr-1" />
            Angle
          </label>
          <textarea
            id="angle"
            name="angle"
            value={formData.angle}
            onChange={handleChange}
            placeholder="e.g., How A2A protocol enables multi-agent collaboration in journalism"
            rows={3}
            className="input-field"
            required
            disabled={isLoading}
          />
        </div>

        <div>
          <label htmlFor="target_length" className="block text-sm font-medium text-gray-700 mb-2">
            <Hash className="h-4 w-4 inline mr-1" />
            Word Count
          </label>
          <input
            type="number"
            id="target_length"
            name="target_length"
            value={formData.target_length}
            onChange={handleChange}
            min="100"
            max="5000"
            className="input-field"
            required
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !formData.topic.trim() || !formData.angle.trim()}
          className={`w-full flex items-center justify-center ${
            isLoading || !formData.topic.trim() || !formData.angle.trim()
              ? 'btn-secondary opacity-50 cursor-not-allowed'
              : 'btn-primary'
          }`}
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Starting Workflow...
            </>
          ) : (
            <>
              <Send className="h-4 w-4 mr-2" />
              Start News Workflow
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default WorkflowForm;
