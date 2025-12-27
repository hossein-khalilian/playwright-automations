'use client';

import { useState } from 'react';
import { sourceApi } from '@/lib/api-client';
import type { Source } from '@/lib/types';
import SourceReviewModal from './SourceReviewModal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, RefreshCw, Trash2, FileEdit, Eye } from 'lucide-react';

interface SourceManagerProps {
  notebookId: string;
  sources: Source[];
  onSourcesChange: () => void;
  loading?: boolean;
}

export default function SourceManager({
  notebookId,
  sources,
  onSourcesChange,
  loading = false,
}: SourceManagerProps) {
  const [uploading, setUploading] = useState(false);
  const [addingUrls, setAddingUrls] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [urls, setUrls] = useState('');
  const [deleting, setDeleting] = useState<string | null>(null);
  const [renaming, setRenaming] = useState<string | null>(null);
  const [renamingSubmitting, setRenamingSubmitting] = useState<string | null>(null);
  const [newName, setNewName] = useState('');
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError('');
      setInfo('');
    }
    e.target.value = ''; // Reset input to allow selecting the same file again
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setError('');
      setInfo('');
      const status = await sourceApi.upload(notebookId, selectedFile);
      setInfo(status.message || 'Upload submitted. Processing...');
      setSelectedFile(null);
      // Small delay before reloading to allow processing
      await new Promise(resolve => setTimeout(resolve, 1000));
      // Reload sources after upload
      await onSourcesChange();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to upload source';
      setError(errorMessage);
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleAddUrls = async () => {
    if (!urls.trim()) {
      setError('Please enter at least one URL');
      return;
    }

    try {
      setAddingUrls(true);
      setError('');
      setInfo('');
      const status = await sourceApi.addUrls(notebookId, urls.trim());
      setInfo(status.message || 'URLs submitted. Processing...');
      setUrls('');
      // Small delay before reloading to allow processing
      await new Promise(resolve => setTimeout(resolve, 1000));
      // Reload sources after adding URLs
      await onSourcesChange();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to add URL sources';
      setError(errorMessage);
      console.error('Add URLs error:', err);
    } finally {
      setAddingUrls(false);
    }
  };

  const handleDelete = async (sourceName: string) => {
    if (!confirm(`Are you sure you want to delete "${sourceName}"?`)) {
      return;
    }

    try {
      setDeleting(sourceName);
      setError('');
      setInfo('');
      const status = await sourceApi.delete(notebookId, sourceName);
      setInfo(status.message || 'Delete submitted.');
      await onSourcesChange();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to delete source';
      setError(errorMessage);
      console.error('Delete error:', err);
    } finally {
      setDeleting(null);
    }
  };

  const handleRename = async (sourceName: string) => {
    if (renamingSubmitting) return;
    if (!newName.trim()) {
      setRenaming(null);
      return;
    }

    try {
      setRenamingSubmitting(sourceName);
      setError('');
      setInfo('');
      const status = await sourceApi.rename(notebookId, sourceName, newName.trim());
      setInfo(status.message || 'Rename submitted.');
      setRenaming(null);
      setNewName('');
      await onSourcesChange();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to rename source';
      setError(errorMessage);
      console.error('Rename error:', err);
    } finally {
      setRenamingSubmitting(null);
    }
  };


  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {info && !error && (
        <Alert>
          <AlertDescription>{info}</AlertDescription>
        </Alert>
      )}

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Source</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Input
              type="file"
              onChange={handleFileSelect}
              disabled={uploading}
            />
          </div>
          {selectedFile && (
            <div className="flex items-center justify-between rounded-md border bg-muted p-3">
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">{selectedFile.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  onClick={() => setSelectedFile(null)}
                  disabled={uploading}
                  variant="outline"
                  size="sm"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleFileUpload}
                  disabled={uploading}
                  size="sm"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    'Upload'
                  )}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add URLs Section */}
      <Card>
        <CardHeader>
          <CardTitle>Add URL Sources</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            placeholder="Paste URLs here, one per line or separated by spaces&#10;Example:&#10;https://example.com/page1&#10;https://example.com/page2"
            disabled={addingUrls}
            rows={6}
          />
          <div className="flex items-center justify-end">
            <Button
              onClick={handleAddUrls}
              disabled={addingUrls || !urls.trim()}
            >
              {addingUrls ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Adding...
                </>
              ) : (
                'Add URLs'
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            To add multiple URLs, separate them with a new line or space.
          </p>
        </CardContent>
      </Card>

      {/* Sources List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Sources</CardTitle>
            <div className="flex items-center space-x-2">
              {loading && (
                <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Loading...</span>
                </div>
              )}
              <Button
                onClick={onSourcesChange}
                disabled={loading}
                variant="outline"
                size="sm"
                title="Reload sources"
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                Reload
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading && sources.length === 0 ? (
            <div className="text-center py-8">
              <Loader2 className="inline-block h-8 w-8 animate-spin" />
              <p className="mt-4 text-muted-foreground">Loading sources...</p>
            </div>
          ) : sources.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              No sources uploaded yet. Upload a file to get started.
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {sources.map((source) => (
                <li key={source.name} className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-sm font-medium text-foreground">{source.name}</h3>
                        <Badge
                          variant={
                            source.status === 'ready'
                              ? 'default'
                              : source.status === 'processing'
                              ? 'secondary'
                              : 'outline'
                          }
                        >
                          {source.status}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {renaming === source.name ? (
                        <div className="flex items-center space-x-2">
                          <Input
                            type="text"
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            disabled={renamingSubmitting === source.name}
                            placeholder="New name"
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                handleRename(source.name);
                              } else if (e.key === 'Escape') {
                                setRenaming(null);
                                setNewName('');
                              }
                            }}
                            className="w-32"
                          />
                          <Button
                            onClick={() => handleRename(source.name)}
                            disabled={renamingSubmitting === source.name}
                            size="sm"
                          >
                            {renamingSubmitting === source.name ? (
                              <>
                                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                Saving...
                              </>
                            ) : (
                              'Save'
                            )}
                          </Button>
                          <Button
                            onClick={() => {
                              setRenaming(null);
                              setNewName('');
                            }}
                            disabled={renamingSubmitting === source.name}
                            variant="outline"
                            size="sm"
                          >
                            Cancel
                          </Button>
                        </div>
                      ) : (
                        <>
                          <Button
                            onClick={() => setSelectedSource(source.name)}
                            size="sm"
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            Review
                          </Button>
                          <Button
                            onClick={() => {
                              setRenaming(source.name);
                              setNewName(source.name);
                            }}
                            variant="outline"
                            size="sm"
                          >
                            <FileEdit className="h-4 w-4 mr-1" />
                            Rename
                          </Button>
                          <Button
                            onClick={() => handleDelete(source.name)}
                            disabled={deleting === source.name}
                            variant="destructive"
                            size="sm"
                          >
                            {deleting === source.name ? (
                              <>
                                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                                Deleting...
                              </>
                            ) : (
                              <>
                                <Trash2 className="h-4 w-4 mr-1" />
                                Delete
                              </>
                            )}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {selectedSource && (
        <SourceReviewModal
          notebookId={notebookId}
          sourceName={selectedSource}
          onClose={() => setSelectedSource(null)}
        />
      )}
    </div>
  );
}

