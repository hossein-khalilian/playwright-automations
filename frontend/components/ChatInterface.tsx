'use client';

import { useState, useRef, useEffect, useMemo } from 'react';
import { chatApi } from '@/lib/api-client';
import type { ChatMessage } from '@/lib/types';
import ReactMarkdown from 'react-markdown';
import { getTextDirection } from '@/lib/rtl-utils';

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
      await chatApi.query(notebookId, query);
      setQuery('');
      // Reload messages after a short delay to allow processing
      setTimeout(() => {
        onMessagesChange();
      }, 1000);
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
      setError('');
      await chatApi.deleteHistory(notebookId);
      onMessagesChange();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to delete chat history';
      setError(errorMessage);
      console.error('Delete history error:', err);
    }
  };

  return (
    <div className="flex h-[600px] flex-col rounded-lg bg-white shadow">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
        <div className="flex items-center space-x-2">
          <h2 className="text-xl font-semibold text-gray-900">Chat</h2>
          {loading && (
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent"></div>
              <span>Loading...</span>
            </div>
          )}
        </div>
        <button
          onClick={handleDeleteHistory}
          className="rounded-md bg-red-600 px-3 py-1 text-xs font-semibold text-white hover:bg-red-500"
        >
          Clear History
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {loading && messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"></div>
            <p className="mt-4">Loading chat history...</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
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
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                  dir={messageRTL}
                >
                  <div className={`prose prose-sm max-w-none ${
                    message.role === 'user' 
                      ? 'prose-invert prose-headings:text-white prose-p:text-white prose-strong:text-white prose-ul:text-white prose-ol:text-white prose-li:text-white'
                      : 'prose-headings:text-gray-900 prose-p:text-gray-900 prose-strong:text-gray-900 prose-ul:text-gray-900 prose-ol:text-gray-900 prose-li:text-gray-900'
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
      </div>

      {/* Input */}
      {error && (
        <div className="px-6 py-2">
          <div className="rounded-md bg-red-50 p-2">
            <div className="text-xs text-red-800">{error}</div>
          </div>
        </div>
      )}

      <form onSubmit={handleSend} className="border-t border-gray-200 px-6 py-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            dir={queryRTL}
            disabled={sending || loading}
          />
          <button
            type="submit"
            disabled={sending || !query.trim() || loading}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 flex items-center space-x-2"
          >
            {sending ? (
              <>
                <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-white border-r-transparent"></div>
                <span>Sending...</span>
              </>
            ) : (
              <span>Send</span>
            )}
          </button>
        </div>
        {sending && (
          <p className="mt-2 text-xs text-gray-500">
            This may take a while. Please wait...
          </p>
        )}
      </form>
    </div>
  );
}

