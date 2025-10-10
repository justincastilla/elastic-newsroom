import React, { useState, useEffect } from 'react';
import { ArrowLeft, FileText, Calendar, User, Tag } from 'lucide-react';

const ArticleViewer = ({ storyId, onBack }) => {
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (storyId) {
      fetchArticle(storyId);
    }
  }, [storyId]);

  const fetchArticle = async (id) => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch from Publisher agent endpoint
      const response = await fetch(`http://localhost:8084/article/${id}`);
      if (response.ok) {
        const articleData = await response.json();
        setArticle(articleData);
      } else {
        throw new Error(`Article not found: ${response.status} ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error fetching article:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading article...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Article Not Found</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={onBack}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-400 text-6xl mb-4">📄</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">No Article Data</h2>
          <p className="text-gray-600 mb-4">The article data could not be loaded.</p>
          <button
            onClick={onBack}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={onBack}
              className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </button>
            <div className="flex items-center text-sm text-gray-500">
              <FileText className="h-4 w-4 mr-1" />
              Article Viewer
            </div>
          </div>
        </div>
      </div>

      {/* Article Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <article className="bg-white rounded-lg shadow-sm border p-8">
          {/* Article Header */}
          <header className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4 leading-tight">
              {article.headline || article.title || 'Untitled Article'}
            </h1>
            
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-6">
              {article.published_at && (
                <div className="flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  {new Date(article.published_at).toLocaleDateString()}
                </div>
              )}
              {article.word_count && (
                <div className="flex items-center">
                  <FileText className="h-4 w-4 mr-1" />
                  {article.word_count} words
                </div>
              )}
              {article.story_id && (
                <div className="flex items-center">
                  <Tag className="h-4 w-4 mr-1" />
                  {article.story_id}
                </div>
              )}
            </div>

            {/* Article Meta */}
            {article.topic && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-blue-900 mb-2">Article Details</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-blue-800">Topic:</span>
                    <span className="ml-2 text-blue-700">{article.topic}</span>
                  </div>
                  {article.angle && (
                    <div>
                      <span className="font-medium text-blue-800">Angle:</span>
                      <span className="ml-2 text-blue-700">{article.angle}</span>
                    </div>
                  )}
                  {article.target_length && (
                    <div>
                      <span className="font-medium text-blue-800">Target Length:</span>
                      <span className="ml-2 text-blue-700">{article.target_length} words</span>
                    </div>
                  )}
                  {article.priority && (
                    <div>
                      <span className="font-medium text-blue-800">Priority:</span>
                      <span className="ml-2 text-blue-700">{article.priority}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </header>

          {/* Article Body */}
          <div className="prose prose-lg max-w-none">
            {article.content ? (
              <div 
                className="whitespace-pre-wrap"
                dangerouslySetInnerHTML={{ 
                  __html: article.content.replace(/\n/g, '<br/>') 
                }}
              />
            ) : (
              <div className="text-gray-500 italic">
                No content available for this article.
              </div>
            )}
          </div>

          {/* Article Footer */}
          {article.agents_involved && (
            <footer className="mt-8 pt-6 border-t border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-3">Workflow Information</h3>
              <div className="text-sm text-gray-600">
                <p className="mb-2">
                  <span className="font-medium">Agents Involved:</span> {article.agents_involved.join(', ')}
                </p>
                {article.version && (
                  <p className="mb-2">
                    <span className="font-medium">Version:</span> {article.version}
                  </p>
                )}
                {article.revisions_count && (
                  <p className="mb-2">
                    <span className="font-medium">Revisions:</span> {article.revisions_count}
                  </p>
                )}
                {article.metadata && (
                  <div>
                    <span className="font-medium">Workflow Started:</span>{' '}
                    {article.metadata.workflow_start && 
                      new Date(article.metadata.workflow_start).toLocaleString()
                    }
                  </div>
                )}
              </div>
            </footer>
          )}
        </article>
      </div>
    </div>
  );
};

export default ArticleViewer;
