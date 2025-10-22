import React, { useState, useEffect } from 'react';
import { ArrowLeft, FileText, Calendar, User, Tag } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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

      // Fetch from Article API backend (separate from agent architecture)
      const response = await fetch(`http://localhost:8085/article/${id}`);
      if (response.ok) {
        let articleData = await response.json();

        // Fix headline if it's "Untitled" but content has "HEADLINE:" prefix
        if (articleData.headline === "Untitled" && articleData.content) {
          const lines = articleData.content.split('\n');
          const headlineLine = lines.find(line => line.trim().startsWith('HEADLINE:'));
          if (headlineLine) {
            articleData.headline = headlineLine.replace('HEADLINE:', '').trim();
          }
        }

        // Remove "HEADLINE: ..." line from content since we display it separately
        if (articleData.content) {
          const lines = articleData.content.split('\n');
          const filteredLines = lines.filter(line => !line.trim().startsWith('HEADLINE:'));
          articleData.content = filteredLines.join('\n').trim();
        }

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
          <div className="prose prose-lg prose-slate max-w-none prose-headings:font-bold prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl prose-p:text-gray-700 prose-p:leading-relaxed prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline prose-strong:text-gray-900 prose-strong:font-semibold prose-code:text-sm prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-blockquote:italic prose-ul:list-disc prose-ol:list-decimal">
            {article.content ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Custom component styling
                  h1: ({node, ...props}) => <h1 className="text-3xl font-bold text-gray-900 mt-8 mb-4" {...props} />,
                  h2: ({node, ...props}) => <h2 className="text-2xl font-bold text-gray-900 mt-6 mb-3" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-xl font-semibold text-gray-900 mt-4 mb-2" {...props} />,
                  p: ({node, ...props}) => <p className="text-gray-700 leading-relaxed mb-4" {...props} />,
                  a: ({node, ...props}) => <a className="text-blue-600 hover:text-blue-800 hover:underline" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-semibold text-gray-900" {...props} />,
                  em: ({node, ...props}) => <em className="italic text-gray-700" {...props} />,
                  code: ({node, inline, ...props}) =>
                    inline ? (
                      <code className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
                    ) : (
                      <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto font-mono text-sm" {...props} />
                    ),
                  ul: ({node, ...props}) => <ul className="list-disc list-inside space-y-2 mb-4" {...props} />,
                  ol: ({node, ...props}) => <ol className="list-decimal list-inside space-y-2 mb-4" {...props} />,
                  li: ({node, ...props}) => <li className="text-gray-700" {...props} />,
                  blockquote: ({node, ...props}) => (
                    <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-4 italic text-gray-600 bg-blue-50" {...props} />
                  ),
                }}
              >
                {article.content}
              </ReactMarkdown>
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
