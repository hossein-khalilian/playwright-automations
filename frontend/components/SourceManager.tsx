'use client';

import { useState } from 'react';
import { sourceApi } from '@/lib/api-client';
import type { Source } from '@/lib/types';
import SourceReviewModal from './SourceReviewModal';

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}
      {info && !error && (
        <div className="rounded-md bg-blue-50 p-4">
          <div className="text-sm text-blue-800">{info}</div>
        </div>
      )}

      {/* Upload Section */}
      <div className="rounded-lg bg-white p-6 shadow">
        <h2 className="mb-4 text-xl font-semibold text-gray-900">Upload Source</h2>
        <div className="space-y-4">
          <label className="block">
            <span className="sr-only">Choose file</span>
            <input
              type="file"
              onChange={handleFileSelect}
              disabled={uploading}
              className="block w-full text-sm text-gray-500 file:mr-4 file:rounded-md file:border-0 file:bg-indigo-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-indigo-700 hover:file:bg-indigo-100 disabled:opacity-50"
            />
          </label>
          {selectedFile && (
            <div className="flex items-center justify-between rounded-md border border-gray-300 bg-gray-50 p-3">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setSelectedFile(null)}
                  disabled={uploading}
                  className="rounded-md bg-gray-200 px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-300 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleFileUpload}
                  disabled={uploading}
                  className="rounded-md bg-indigo-600 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
                >
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add URLs Section */}
      <div className="rounded-lg bg-white p-6 shadow">
        <h2 className="mb-4 text-xl font-semibold text-gray-900">Add URL Sources</h2>
        <div className="space-y-4">
          <textarea
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            placeholder="Paste URLs here, one per line or separated by spaces&#10;Example:&#10;https://example.com/page1&#10;https://example.com/page2"
            disabled={addingUrls}
            rows={6}
            className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
          />
          <div className="flex items-center justify-end">
            <button
              onClick={handleAddUrls}
              disabled={addingUrls || !urls.trim()}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {addingUrls ? 'Adding...' : 'Add URLs'}
            </button>
          </div>
          <p className="text-xs text-gray-500">
            To add multiple URLs, separate them with a new line or space.
          </p>
        </div>
      </div>

      {/* Sources List */}
      <div className="rounded-lg bg-white shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Sources</h2>
            <div className="flex items-center space-x-2">
              {loading && (
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent"></div>
                  <span>Loading...</span>
                </div>
              )}
              <button
                onClick={onSourcesChange}
                disabled={loading}
                className="rounded-md bg-indigo-600 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 flex items-center space-x-1"
                title="Reload sources"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <span>Reload</span>
              </button>
            </div>
          </div>
        </div>
        {loading && sources.length === 0 ? (
          <div className="p-6 text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"></div>
            <p className="mt-4 text-gray-600">Loading sources...</p>
          </div>
        ) : sources.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No sources uploaded yet. Upload a file to get started.
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {sources.map((source) => (
              <li key={source.name} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-sm font-medium text-gray-900">{source.name}</h3>
                      <span
                        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(
                          source.status
                        )}`}
                      >
                        {source.status}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {renaming === source.name ? (
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={newName}
                          onChange={(e) => setNewName(e.target.value)}
                          disabled={renamingSubmitting === source.name}
                          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
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
                        />
                        <button
                          onClick={() => handleRename(source.name)}
                          disabled={renamingSubmitting === source.name}
                          className="rounded-md bg-indigo-600 px-2 py-1 text-xs text-white hover:bg-indigo-500 disabled:opacity-50"
                        >
                          {renamingSubmitting === source.name ? 'Saving...' : 'Save'}
                        </button>
                        <button
                          onClick={() => {
                            setRenaming(null);
                            setNewName('');
                          }}
                          disabled={renamingSubmitting === source.name}
                          className="rounded-md bg-gray-200 px-2 py-1 text-xs text-gray-700 hover:bg-gray-300 disabled:opacity-50"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <>
                        <button
                          onClick={() => setSelectedSource(source.name)}
                          className="rounded-md bg-indigo-600 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-500"
                        >
                          Review
                        </button>
                        <button
                          onClick={() => {
                            setRenaming(source.name);
                            setNewName(source.name);
                          }}
                          className="rounded-md bg-gray-200 px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-300"
                        >
                          Rename
                        </button>
                        <button
                          onClick={() => handleDelete(source.name)}
                          disabled={deleting === source.name}
                          className="rounded-md bg-red-600 px-3 py-1 text-xs font-semibold text-white hover:bg-red-500 disabled:opacity-50"
                        >
                          {deleting === source.name ? 'Deleting...' : 'Delete'}
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

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

