'use client';

import { useEffect, useState } from 'react';
import { useRouter } from '@/lib/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslations, useLocale } from 'next-intl';
import { notebookApi } from '@/lib/api-client';
import type { Notebook } from '@/lib/types';
import Navbar from '@/components/Navbar';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Plus, Trash2, FolderOpen, Pencil, Check, X } from 'lucide-react';
import { Input } from '@/components/ui/input';

export default function NotebooksPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const locale = useLocale();
  const isRTL = locale === 'fa';
  const t = useTranslations('notebooks');
  const tCommon = useTranslations('common');
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState<string>('');
  const [renamingId, setRenamingId] = useState<string | null>(null);
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
      setError(err.response?.data?.detail || t('loadFailed'));
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
      setInfo(status.message || t('createSubmitted'));
      await loadNotebooks();
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || t('createFailed');
      setError(message);
    } finally {
      setCreating(false);
    }
  };

  const handleStartEdit = (notebook: Notebook) => {
    setEditingId(notebook.notebook_id);
    setEditingTitle(notebook.title || '');
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditingTitle('');
  };

  const handleSaveRename = async (notebookId: string) => {
    if (!editingTitle.trim()) {
      return;
    }

    try {
      setRenamingId(notebookId);
      setError('');
      setInfo('');
      const status = await notebookApi.rename(notebookId, editingTitle.trim());
      setInfo(status.message || t('renameSubmitted'));
      setEditingId(null);
      setEditingTitle('');
      setRenamingId(null);
      await loadNotebooks();
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || t('renameFailed');
      setError(message);
      setRenamingId(null);
    }
  };

  const handleDelete = async (notebookId: string) => {
    if (deletingId) return;
    if (!confirm(t('deleteConfirm'))) {
      return;
    }

    try {
      setDeletingId(notebookId);
      setInfo('');
      const status = await notebookApi.delete(notebookId);
      setInfo(status.message || t('deleteSubmitted'));
      await loadNotebooks();
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || t('deleteFailed');
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
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-3xl font-bold text-foreground">{t('title')}</h1>
            <Button
              onClick={handleCreate}
              disabled={creating}
            >
              {creating ? (
                <>
                  <Loader2 className={`h-4 w-4 ${isRTL ? 'ml-2' : 'mr-2'} animate-spin`} />
                  {t('creating')}
                </>
              ) : (
                <>
                  <Plus className={`h-4 w-4 ${isRTL ? 'ml-2' : 'mr-2'}`} />
                  {t('createNotebook')}
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
                <p className="text-muted-foreground">{t('noNotebooks')}</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {notebooks.map((notebook) => (
                <Card key={notebook.notebook_id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    {editingId === notebook.notebook_id ? (
                      <div className="flex items-center gap-2">
                        <Input
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleSaveRename(notebook.notebook_id);
                            } else if (e.key === 'Escape') {
                              handleCancelEdit();
                            }
                          }}
                          className="flex-1"
                          autoFocus
                        />
                        <Button
                          onClick={() => handleSaveRename(notebook.notebook_id)}
                          disabled={!editingTitle.trim() || renamingId === notebook.notebook_id}
                          size="icon"
                          variant="default"
                          title={t('saveRename')}
                        >
                          {renamingId === notebook.notebook_id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Check className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          onClick={handleCancelEdit}
                          disabled={renamingId === notebook.notebook_id}
                          size="icon"
                          variant="outline"
                          title={tCommon('cancel')}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ) : (
                      <CardTitle className="text-lg line-clamp-2 min-h-[3rem] break-words">
                        {notebook.title || t('untitledNotebook')}
                      </CardTitle>
                    )}
                    <CardDescription>
                      {t('created')}: {format(new Date(notebook.created_at), 'PPp')}
                    </CardDescription>
                  </CardHeader>
                  <CardFooter className={`flex ${isRTL ? 'space-x-reverse space-x-2' : 'space-x-2'}`}>
                    <Button
                      onClick={() => router.push(`/notebooks/${notebook.notebook_id}`)}
                      className="flex-1"
                      disabled={editingId === notebook.notebook_id}
                    >
                      <FolderOpen className={`h-4 w-4 ${isRTL ? 'ml-2' : 'mr-2'}`} />
                      {tCommon('open')}
                    </Button>
                    {editingId !== notebook.notebook_id && (
                      <>
                        <Button
                          onClick={() => handleStartEdit(notebook)}
                          disabled={renamingId === notebook.notebook_id || deletingId === notebook.notebook_id}
                          variant="outline"
                          size="icon"
                          title={tCommon('edit')}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          onClick={() => handleDelete(notebook.notebook_id)}
                          disabled={deletingId === notebook.notebook_id || renamingId === notebook.notebook_id}
                          variant="destructive"
                          size="icon"
                          title={tCommon('delete')}
                        >
                          {deletingId === notebook.notebook_id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </>
                    )}
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

