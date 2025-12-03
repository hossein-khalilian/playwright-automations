'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { notebookApi } from '@/lib/api-client';
import type { Notebook } from '@/lib/types';
import Navbar from '@/components/Navbar';
import { format } from 'date-fns';

export default function NotebooksPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

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
      const response = await notebookApi.create();
      if (response.notebook_url) {
        // Extract notebook_id from URL or reload list
        await loadNotebooks();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create notebook');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (notebookId: string) => {
    if (!confirm('Are you sure you want to delete this notebook?')) {
      return;
    }

    try {
      await notebookApi.delete(notebookId);
      await loadNotebooks();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete notebook');
    }
  };

  if (authLoading || loading) {
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
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">My Notebooks</h1>
            <button
              onClick={handleCreate}
              disabled={creating}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {creating ? 'Creating...' : 'Create Notebook'}
            </button>
          </div>

          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}

          {notebooks.length === 0 ? (
            <div className="rounded-lg bg-white p-12 text-center shadow">
              <p className="text-gray-500">No notebooks yet. Create your first notebook!</p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {notebooks.map((notebook) => (
                <div
                  key={notebook.notebook_id}
                  className="rounded-lg bg-white p-6 shadow hover:shadow-md transition-shadow"
                >
                  <h3 className="mb-2 text-lg font-semibold text-gray-900">
                    {notebook.notebook_id}
                  </h3>
                  <p className="mb-4 text-sm text-gray-500">
                    Created: {format(new Date(notebook.created_at), 'PPp')}
                  </p>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => router.push(`/notebooks/${notebook.notebook_id}`)}
                      className="flex-1 rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
                    >
                      Open
                    </button>
                    <button
                      onClick={() => handleDelete(notebook.notebook_id)}
                      className="rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-500"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

