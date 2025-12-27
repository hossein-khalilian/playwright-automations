'use client';

import { useState, useEffect, useMemo } from 'react';
import { sourceApi } from '@/lib/api-client';
import ReactMarkdown from 'react-markdown';
import { getRTLClasses, getTextDirection } from '@/lib/rtl-utils';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';

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
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Source Review: {sourceName}</DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="text-center py-8">
            <Loader2 className="inline-block h-8 w-8 animate-spin" />
            <p className="mt-4 text-muted-foreground">Loading... This may take a moment.</p>
          </div>
        ) : error ? (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : data ? (
          <div 
            className="space-y-4"
            dir={contentRTL || 'ltr'}
          >
            {data.message && (
              <Alert>
                <AlertDescription>{data.message}</AlertDescription>
              </Alert>
            )}
            {data.title && (
              <div>
                <h4 className="font-semibold text-foreground">Title</h4>
                <p 
                  className="text-foreground"
                  dir={getTextDirection(data.title)}
                >
                  {data.title}
                </p>
              </div>
            )}

            {data.summary && (
              <div>
                <h4 className="font-semibold text-foreground">Summary</h4>
                <div 
                  className="prose max-w-none prose-gray prose-headings:text-foreground prose-p:text-foreground prose-strong:text-foreground prose-ul:text-foreground prose-ol:text-foreground prose-li:text-foreground"
                  dir={getTextDirection(data.summary)}
                >
                  <ReactMarkdown>{data.summary}</ReactMarkdown>
                </div>
              </div>
            )}

            {data.key_topics && data.key_topics.length > 0 && (
              <div>
                <h4 className="font-semibold text-foreground">Key Topics</h4>
                <ul className={`list-disc space-y-1 ${contentRTL === 'rtl' ? 'list-inside pr-6' : 'list-inside pl-6'}`}>
                  {data.key_topics.map((topic: string, idx: number) => {
                    const topicRTL = getTextDirection(topic);
                    return (
                      <li 
                        key={idx} 
                        className="text-foreground"
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
                <h4 className="font-semibold text-foreground">Content</h4>
                <div 
                  className="prose max-w-none prose-gray prose-headings:text-foreground prose-p:text-foreground prose-strong:text-foreground prose-ul:text-foreground prose-ol:text-foreground prose-li:text-foreground"
                  dir={getTextDirection(data.content)}
                >
                  <ReactMarkdown>{data.content}</ReactMarkdown>
                </div>
              </div>
            )}

            {data.images && data.images.length > 0 && (
              <div>
                <h4 className="font-semibold text-foreground">Images</h4>
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
      </DialogContent>
    </Dialog>
  );
}

