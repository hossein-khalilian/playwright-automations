'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  sourceApi,
  chatApi,
  artifactApi,
} from '@/lib/api-client';
import type {
  Source,
  ArtifactInfo,
  ChatMessage,
} from '@/lib/types';
import Navbar from '@/components/Navbar';
import SourceManager from '@/components/SourceManager';
import ChatInterface from '@/components/ChatInterface';
import ArtifactManager from '@/components/ArtifactManager';

export default function NotebookDetailPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const notebookId = params.id as string;

  const [activeTab, setActiveTab] = useState<'sources' | 'chat' | 'artifacts'>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(`notebook-active-tab-${params.id as string}`);
      if (stored === 'sources' || stored === 'chat' || stored === 'artifacts') {
        return stored;
      }
    }
    return 'sources';
  });
  const [sources, setSources] = useState<Source[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactInfo[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingSources, setLoadingSources] = useState(false);
  const [loadingArtifacts, setLoadingArtifacts] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const [loadedTabs, setLoadedTabs] = useState<Set<string>>(new Set());
  const [error, setError] = useState('');

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }
  }, [isAuthenticated, authLoading, router]);

  // Persist active tab per notebook to localStorage
  useEffect(() => {
    if (!notebookId) return;
    localStorage.setItem(`notebook-active-tab-${notebookId}`, activeTab);
  }, [notebookId, activeTab]);

  const loadSources = async () => {
    try {
      setLoadingSources(true);
      setError('');
      const response = await sourceApi.list(notebookId);
      setSources(response.sources);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load sources';
      setError(errorMessage);
      console.error('Failed to load sources:', err);
    } finally {
      setLoadingSources(false);
    }
  };

  const loadArtifacts = async () => {
    try {
      setLoadingArtifacts(true);
      setError('');
      const response = await artifactApi.list(notebookId);
      setArtifacts(response.artifacts);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load artifacts';
      setError(errorMessage);
      console.error('Failed to load artifacts:', err);
    } finally {
      setLoadingArtifacts(false);
    }
  };

  const loadChatHistory = async () => {
    try {
      setLoadingChat(true);
      setError('');
      const response = await chatApi.getHistory(notebookId);
      setChatMessages(response.messages);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load chat history';
      setError(errorMessage);
      console.error('Failed to load chat history:', err);
    } finally {
      setLoadingChat(false);
    }
  };

  const loadTabData = useCallback(async (tab: 'sources' | 'chat' | 'artifacts') => {
    // Small delay to allow browser to be ready
    await new Promise(resolve => setTimeout(resolve, 300));
    
    switch (tab) {
      case 'sources':
        try {
          setLoadingSources(true);
          setError('');
          const response = await sourceApi.list(notebookId);
          setSources(response.sources);
        } catch (err: any) {
          const errorMessage = err.response?.data?.detail || err.message || 'Failed to load sources';
          setError(errorMessage);
          console.error('Failed to load sources:', err);
        } finally {
          setLoadingSources(false);
        }
        break;
      case 'artifacts':
        try {
          setLoadingArtifacts(true);
          setError('');
          const response = await artifactApi.list(notebookId);
          setArtifacts(response.artifacts);
        } catch (err: any) {
          const errorMessage = err.response?.data?.detail || err.message || 'Failed to load artifacts';
          setError(errorMessage);
          console.error('Failed to load artifacts:', err);
        } finally {
          setLoadingArtifacts(false);
        }
        break;
      case 'chat':
        try {
          setLoadingChat(true);
          setError('');
          const response = await chatApi.getHistory(notebookId);
          setChatMessages(response.messages);
        } catch (err: any) {
          const errorMessage = err.response?.data?.detail || err.message || 'Failed to load chat history';
          setError(errorMessage);
          console.error('Failed to load chat history:', err);
        } finally {
          setLoadingChat(false);
        }
        break;
    }
    
    // Mark tab as loaded
    setLoadedTabs(prev => new Set(prev).add(tab));
  }, [notebookId]);

  // Load data when tab is activated (lazy loading)
  useEffect(() => {
    if (isAuthenticated && notebookId && !loadedTabs.has(activeTab)) {
      loadTabData(activeTab);
    }
  }, [isAuthenticated, notebookId, activeTab, loadedTabs, loadTabData]);

  if (authLoading) {
    return (
      <>
        <Navbar />
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="mb-6">
            <button
              onClick={() => router.push('/notebooks')}
              className="mb-4 text-sm text-indigo-600 hover:text-indigo-500"
            >
              ← Back to Notebooks
            </button>
            <h1 className="text-3xl font-bold text-gray-900">Notebook: {notebookId}</h1>
          </div>

          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
              <div className="flex items-center justify-between">
                <div className="text-sm text-red-800">{error}</div>
                <button
                  onClick={() => {
                    setError('');
                    loadTabData(activeTab);
                  }}
                  className="ml-4 rounded-md bg-red-600 px-3 py-1 text-xs font-semibold text-white hover:bg-red-500"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="mb-6 border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => {
                  setActiveTab('sources');
                  // Load if not already loaded
                  if (!loadedTabs.has('sources')) {
                    loadTabData('sources');
                  }
                }}
                className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                  activeTab === 'sources'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                Sources
              </button>
              <button
                onClick={() => {
                  setActiveTab('chat');
                  // Load if not already loaded
                  if (!loadedTabs.has('chat')) {
                    loadTabData('chat');
                  }
                }}
                className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                  activeTab === 'chat'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => {
                  setActiveTab('artifacts');
                  // Load if not already loaded
                  if (!loadedTabs.has('artifacts')) {
                    loadTabData('artifacts');
                  }
                }}
                className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                  activeTab === 'artifacts'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                Artifacts
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          <div>
            {activeTab === 'sources' && (
              <SourceManager
                notebookId={notebookId}
                sources={sources}
                onSourcesChange={loadSources}
                loading={loadingSources}
              />
            )}
            {activeTab === 'chat' && (
              <ChatInterface
                notebookId={notebookId}
                messages={chatMessages}
                onMessagesChange={loadChatHistory}
                loading={loadingChat}
              />
            )}
            {activeTab === 'artifacts' && (
              <ArtifactManager
                notebookId={notebookId}
                artifacts={artifacts}
                onArtifactsChange={loadArtifacts}
                loading={loadingArtifacts}
              />
            )}
          </div>
        </div>
      </div>
    </>
  );
}

