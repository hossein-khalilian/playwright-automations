'use client';

import { useState, useEffect } from 'react';
import { sourceApi } from '@/lib/api-client';
import ReactMarkdown from 'react-markdown';

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

  useEffect(() => {
    loadReview();
  }, [notebookId, sourceName]);

  const loadReview = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await sourceApi.review(notebookId, sourceName);
      setData(response);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load source review';
      setError(errorMessage);
      console.error('Review error:', err);
    } finally {
      setLoading(false);
    }
  };

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
              <div className="space-y-4 max-h-[70vh] overflow-y-auto">
                {data.title && (
                  <div>
                    <h4 className="font-semibold text-gray-900">Title</h4>
                    <p className="text-gray-700">{data.title}</p>
                  </div>
                )}

                {data.summary && (
                  <div>
                    <h4 className="font-semibold text-gray-900">Summary</h4>
                    <div className="prose max-w-none">
                      <ReactMarkdown>{data.summary}</ReactMarkdown>
                    </div>
                  </div>
                )}

                {data.key_topics && data.key_topics.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900">Key Topics</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {data.key_topics.map((topic: string, idx: number) => (
                        <li key={idx} className="text-gray-700">{topic}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {data.content && (
                  <div>
                    <h4 className="font-semibold text-gray-900">Content</h4>
                    <div className="prose max-w-none">
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

