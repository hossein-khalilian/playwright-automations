'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from '@/lib/navigation';
import { useParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslations } from 'next-intl';
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
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, ArrowLeft } from 'lucide-react';

export default function NotebookDetailPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const notebookId = params.id as string;
  const t = useTranslations('notebooks');
  const tCommon = useTranslations('common');
  const tSources = useTranslations('sources');
  const tChat = useTranslations('chat');
  const tArtifacts = useTranslations('artifacts');

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
      const errorMessage = err.response?.data?.detail || err.message || tSources('loadFailed');
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
      const errorMessage = err.response?.data?.detail || err.message || tArtifacts('loadFailed');
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
      const errorMessage = err.response?.data?.detail || err.message || tChat('loadFailed');
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
          const errorMessage = err.response?.data?.detail || err.message || tSources('loadFailed');
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
          const errorMessage = err.response?.data?.detail || err.message || tArtifacts('loadFailed');
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
          const errorMessage = err.response?.data?.detail || err.message || tChat('loadFailed');
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
            <Loader2 className="inline-block h-8 w-8 animate-spin" />
            <p className="mt-4 text-muted-foreground">{tCommon('loading')}</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-background">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="mb-6">
            <Button
              onClick={() => router.push('/notebooks')}
              variant="ghost"
              size="sm"
              className="mb-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              {t('backToNotebooks')}
            </Button>
            <h1 className="text-3xl font-bold text-foreground">{t('notebookDetail', { id: notebookId })}</h1>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription className="flex items-center justify-between">
                <span>{error}</span>
                <Button
                  onClick={() => {
                    setError('');
                    loadTabData(activeTab);
                  }}
                  variant="outline"
                  size="sm"
                  className="ml-4"
                >
                  {tCommon('retry')}
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={(value) => {
            const tab = value as 'sources' | 'chat' | 'artifacts';
            setActiveTab(tab);
            // Load if not already loaded
            if (!loadedTabs.has(tab)) {
              loadTabData(tab);
            }
          }}>
            <TabsList className="mb-6">
              <TabsTrigger value="sources">{tSources('title')}</TabsTrigger>
              <TabsTrigger value="chat">{tChat('title')}</TabsTrigger>
              <TabsTrigger value="artifacts">{tArtifacts('title')}</TabsTrigger>
            </TabsList>

            {/* Tab Content */}
            <TabsContent value="sources">
              <SourceManager
                notebookId={notebookId}
                sources={sources}
                onSourcesChange={loadSources}
                loading={loadingSources}
              />
            </TabsContent>
            <TabsContent value="chat">
              <ChatInterface
                notebookId={notebookId}
                messages={chatMessages}
                onMessagesChange={loadChatHistory}
                loading={loadingChat}
              />
            </TabsContent>
            <TabsContent value="artifacts">
              <ArtifactManager
                notebookId={notebookId}
                artifacts={artifacts}
                onArtifactsChange={loadArtifacts}
                loading={loadingArtifacts}
              />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </>
  );
}

