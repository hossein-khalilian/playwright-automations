'use client';

import { useState, useRef, useEffect, useMemo } from 'react';
import { chatApi } from '@/lib/api-client';
import type { ChatMessage } from '@/lib/types';
import ReactMarkdown from 'react-markdown';
import { getTextDirection } from '@/lib/rtl-utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, RefreshCw, Trash2 } from 'lucide-react';

interface ChatInterfaceProps {
  notebookId: string;
  messages: ChatMessage[];
  onMessagesChange: () => void;
  loading?: boolean;
}

export default function ChatInterface({
  notebookId,
  messages,
  onMessagesChange,
  loading = false,
}: ChatInterfaceProps) {
  const [query, setQuery] = useState('');
  const [sending, setSending] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Detect RTL for the query input
  const queryRTL = useMemo(() => getTextDirection(query), [query]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || sending) return;

    try {
      setSending(true);
      setError('');
      
      // Store the current message count before sending
      const previousMessageCount = messages.length;
      const sentQuery = query;
      
      // Send the query
      await chatApi.query(notebookId, sentQuery);
      setQuery('');
      
      // Initial delay before starting to poll (give the query time to be processed)
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Poll for new messages to appear in chat history
      // We'll check if:
      // 1. The message count has increased (new user message appeared)
      // 2. The last message is from assistant (AI response has been generated)
      const maxAttempts = 30; // Maximum polling attempts (30 * 2s = 60 seconds)
      const pollInterval = 2000; // Poll every 2 seconds
      
      let foundCompleteResponse = false;
      
      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
          // Fetch chat history directly to check for new messages
          const response = await chatApi.getHistory(notebookId);
          const newMessages = response.messages;
          
          // Check if we have new messages
          if (newMessages.length > previousMessageCount) {
            // Check if the last message is from assistant (AI response ready)
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage.role === 'assistant') {
              // Both user message and AI response are ready
              foundCompleteResponse = true;
              // Sync with parent component
              onMessagesChange();
              break;
            }
            // If we have new messages but AI response isn't ready yet, continue polling
          }
        } catch (pollErr) {
          // If polling fails, log but continue
          console.warn('Error polling chat history:', pollErr);
        }
        
        // Wait before next poll attempt
        if (attempt < maxAttempts - 1) {
          await new Promise(resolve => setTimeout(resolve, pollInterval));
        }
      }
      
      // Final update to ensure we have the latest messages (even if AI response isn't ready)
      if (!foundCompleteResponse) {
        onMessagesChange();
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to send query';
      setError(errorMessage);
      console.error('Query error:', err);
    } finally {
      setSending(false);
    }
  };

  const handleDeleteHistory = async () => {
    if (!confirm('Are you sure you want to delete all chat history?')) {
      return;
    }

    try {
      setDeleting(true);
      setError('');
      await chatApi.deleteHistory(notebookId);
      onMessagesChange();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to delete chat history';
      setError(errorMessage);
      console.error('Delete history error:', err);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Card className="flex h-[600px] flex-col">
      {/* Header */}
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <div className="flex items-center space-x-2">
          <CardTitle>Chat</CardTitle>
          {loading && (
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading...</span>
            </div>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            onClick={onMessagesChange}
            disabled={loading || sending}
            variant="outline"
            size="sm"
            title="Reload chat history"
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Reload
          </Button>
          <Button
            onClick={handleDeleteHistory}
            disabled={deleting || loading || sending}
            variant="destructive"
            size="icon"
            title="Clear History"
          >
            {deleting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      {/* Messages */}
      <CardContent className="flex-1 overflow-y-auto space-y-4">
        {loading && messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            <Loader2 className="inline-block h-8 w-8 animate-spin" />
            <p className="mt-4">Loading chat history...</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            No messages yet. Start a conversation!
          </div>
        ) : (
          messages.map((message, idx) => {
            const messageRTL = getTextDirection(message.content);
            return (
              <div
                key={idx}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-foreground'
                  }`}
                  dir={messageRTL}
                >
                  <div className={`prose prose-sm max-w-none ${
                    message.role === 'user' 
                      ? 'prose-invert prose-headings:text-primary-foreground prose-p:text-primary-foreground prose-strong:text-primary-foreground prose-ul:text-primary-foreground prose-ol:text-primary-foreground prose-li:text-primary-foreground'
                      : 'prose-headings:text-foreground prose-p:text-foreground prose-strong:text-foreground prose-ul:text-foreground prose-ol:text-foreground prose-li:text-foreground'
                  }`}>
                    <ReactMarkdown>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </CardContent>

      {/* Input */}
      {error && (
        <div className="px-6 py-2">
          <Alert variant="destructive">
            <AlertDescription className="text-xs">{error}</AlertDescription>
          </Alert>
        </div>
      )}

      <form onSubmit={handleSend} className="border-t px-6 py-4">
        <div className="flex space-x-2">
          <Input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question..."
            dir={queryRTL}
            disabled={sending || loading}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={sending || !query.trim() || loading}
          >
            {sending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Sending...
              </>
            ) : (
              'Send'
            )}
          </Button>
        </div>
        {sending && (
          <p className="mt-2 text-xs text-muted-foreground">
            This may take a while. Please wait...
          </p>
        )}
      </form>
    </Card>
  );
}

