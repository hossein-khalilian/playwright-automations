'use client';

import { useState, useEffect, useMemo } from 'react';
import { sourceApi } from '@/lib/api-client';
import ReactMarkdown from 'react-markdown';
import { getRTLClasses, getTextDirection } from '@/lib/rtl-utils';

interface SourceReviewModalProps {
  notebookId: string;
  sourceName: string;
  onClose: () => void;
}

export default function SourceReviewModal({
  notebookId,
  sourceName,
  onClose,
}: SourceReviewModalProps) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');

  // Detect RTL for the content
  const contentRTL = useMemo(() => {
    if (!data) return null;
    const allText = [
      data.title,
      data.summary,
      data.content,
      ...(data.key_topics || []),
    ].filter(Boolean).join(' ');
    return getTextDirection(allText);
  }, [data]);

  useEffect(() => {
    const loadReview = async () => {
      try {
        setLoading(true);
        setError('');
        const status = await sourceApi.review(notebookId, sourceName);
        if (status.result) {
          setData(status.result);
        } else if (status.message) {
          setData({
            status: 'info',
            message: status.message,
            key_topics: [],
            images: [],
          });
        } else {
          setError('Review completed but no details were returned.');
        }
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail || err.message || 'Failed to load source review';
        setError(errorMessage);
        console.error('Review error:', err);
      } finally {
        setLoading(false);
      }
    };
    loadReview();
  }, [notebookId, sourceName]);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose}></div>

        <div className="inline-block transform overflow-hidden rounded-lg bg-white text-left align-bottom shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl sm:align-middle">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium leading-6 text-gray-900">
                Source Review: {sourceName}
              </h3>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-500"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {loading ? (
              <div className="text-center py-8">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"></div>
                <p className="mt-4 text-gray-600">Loading... This may take a moment.</p>
              </div>
            ) : error ? (
              <div className="rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-800">{error}</div>
              </div>
            ) : data ? (
              <div 
                className="space-y-4 max-h-[70vh] overflow-y-auto"
                dir={contentRTL || 'ltr'}
              >
                {data.message && (
                  <div className="rounded-md bg-blue-50 p-3 text-sm text-blue-800">
                    {data.message}
                  </div>
                )}
                {data.title && (
                  <div>
                    <h4 className="font-semibold text-gray-900">Title</h4>
                    <p 
                      className="text-gray-700"
                      dir={getTextDirection(data.title)}
                    >
                      {data.title}
                    </p>
                  </div>
                )}

                {data.summary && (
                  <div>
                    <h4 className="font-semibold text-gray-900">Summary</h4>
                    <div 
                      className="prose max-w-none prose-gray prose-headings:text-gray-900 prose-p:text-gray-900 prose-strong:text-gray-900 prose-ul:text-gray-900 prose-ol:text-gray-900 prose-li:text-gray-900"
                      dir={getTextDirection(data.summary)}
                    >
                      <ReactMarkdown>{data.summary}</ReactMarkdown>
                    </div>
                  </div>
                )}

                {data.key_topics && data.key_topics.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900">Key Topics</h4>
                    <ul className={`list-disc space-y-1 ${contentRTL === 'rtl' ? 'list-inside pr-6' : 'list-inside pl-6'}`}>
                      {data.key_topics.map((topic: string, idx: number) => {
                        const topicRTL = getTextDirection(topic);
                        return (
                          <li 
                            key={idx} 
                            className="text-gray-700"
                            dir={topicRTL}
                          >
                            {topic}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}

                {data.content && (
                  <div>
                    <h4 className="font-semibold text-gray-900">Content</h4>
                    <div 
                      className="prose max-w-none prose-gray prose-headings:text-gray-900 prose-p:text-gray-900 prose-strong:text-gray-900 prose-ul:text-gray-900 prose-ol:text-gray-900 prose-li:text-gray-900"
                      dir={getTextDirection(data.content)}
                    >
                      <ReactMarkdown>{data.content}</ReactMarkdown>
                    </div>
                  </div>
                )}

                {data.images && data.images.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900">Images</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {data.images.map((img: any, idx: number) => (
                        <div key={idx}>
                          {img.base64 && (
                            <img
                              src={`data:${img.mime_type || 'image/png'};base64,${img.base64}`}
                              alt={`Image ${idx + 1}`}
                              className="max-w-full h-auto rounded"
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

