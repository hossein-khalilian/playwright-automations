'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { notebookApi } from '@/lib/api-client';
import type { Notebook } from '@/lib/types';
import Navbar from '@/components/Navbar';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Plus, Trash2, FolderOpen } from 'lucide-react';

export default function NotebooksPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }

    if (isAuthenticated) {
      loadNotebooks();
    }
  }, [isAuthenticated, authLoading, router]);

  const loadNotebooks = async () => {
    try {
      setLoading(true);
      const response = await notebookApi.list();
      setNotebooks(response.notebooks);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load notebooks');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      setCreating(true);
      setError('');
      setInfo('');
      const status = await notebookApi.create();
      setInfo(status.message || 'Notebook creation submitted.');
      await loadNotebooks();
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to create notebook';
      setError(message);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (notebookId: string) => {
    if (deletingId) return;
    if (!confirm('Are you sure you want to delete this notebook?')) {
      return;
    }

    try {
      setDeletingId(notebookId);
      setInfo('');
      const status = await notebookApi.delete(notebookId);
      setInfo(status.message || 'Notebook deletion submitted.');
      await loadNotebooks();
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to delete notebook';
      setError(message);
    } finally {
      setDeletingId(null);
    }
  };

  if (authLoading || loading) {
    return (
      <>
        <Navbar />
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <Loader2 className="inline-block h-8 w-8 animate-spin" />
            <p className="mt-4 text-muted-foreground">Loading...</p>
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
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-3xl font-bold text-foreground">My Notebooks</h1>
            <Button
              onClick={handleCreate}
              disabled={creating}
            >
              {creating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Notebook
                </>
              )}
            </Button>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {info && !error && (
            <Alert className="mb-4">
              <AlertDescription>{info}</AlertDescription>
            </Alert>
          )}

          {notebooks.length === 0 ? (
            <Card className="p-12 text-center">
              <CardContent>
                <p className="text-muted-foreground">No notebooks yet. Create your first notebook!</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {notebooks.map((notebook) => (
                <Card key={notebook.notebook_id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <CardTitle className="text-lg">{notebook.notebook_id}</CardTitle>
                    <CardDescription>
                      Created: {format(new Date(notebook.created_at), 'PPp')}
                    </CardDescription>
                  </CardHeader>
                  <CardFooter className="flex space-x-2">
                    <Button
                      onClick={() => router.push(`/notebooks/${notebook.notebook_id}`)}
                      className="flex-1"
                    >
                      <FolderOpen className="h-4 w-4 mr-2" />
                      Open
                    </Button>
                    <Button
                      onClick={() => handleDelete(notebook.notebook_id)}
                      disabled={deletingId === notebook.notebook_id}
                      variant="destructive"
                    >
                      {deletingId === notebook.notebook_id ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Deleting...
                        </>
                      ) : (
                        <>
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </>
                      )}
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

