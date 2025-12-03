'use client';

import { useState } from 'react';
import { artifactApi } from '@/lib/api-client';
import type { ArtifactInfo } from '@/lib/types';
import ArtifactCreateModal from './ArtifactCreateModal';

interface ArtifactManagerProps {
  notebookId: string;
  artifacts: ArtifactInfo[];
  onArtifactsChange: () => void;
  loading?: boolean;
}

export default function ArtifactManager({
  notebookId,
  artifacts,
  onArtifactsChange,
  loading = false,
}: ArtifactManagerProps) {
  const [deleting, setDeleting] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [createType, setCreateType] = useState<string | null>(null);
  const [error, setError] = useState('');

  const handleDelete = async (artifactName: string) => {
    if (!confirm(`Are you sure you want to delete "${artifactName}"?`)) {
      return;
    }

    try {
      setDeleting(artifactName);
      setError('');
      await artifactApi.delete(notebookId, artifactName);
      await onArtifactsChange();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to delete artifact';
      setError(errorMessage);
      console.error('Delete artifact error:', err);
    } finally {
      setDeleting(null);
    }
  };

  const handleDownload = async (artifactName: string) => {
    try {
      setDownloading(artifactName);
      setError('');
      const blob = await artifactApi.download(notebookId, artifactName);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = artifactName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to download artifact';
      setError(errorMessage);
      console.error('Download error:', err);
    } finally {
      setDownloading(null);
    }
  };

  const getStatusColor = (status: string, isGenerating: boolean) => {
    if (isGenerating) {
      return 'bg-yellow-100 text-yellow-800';
    }
    switch (status) {
      case 'ready':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const artifactTypes = [
    { id: 'audio-overview', label: 'Audio Overview' },
    { id: 'video-overview', label: 'Video Overview' },
    { id: 'flashcards', label: 'Flashcards' },
    { id: 'quiz', label: 'Quiz' },
    { id: 'infographic', label: 'Infographic' },
    { id: 'slide-deck', label: 'Slide Deck' },
    { id: 'report', label: 'Report' },
    { id: 'mindmap', label: 'Mind Map' },
  ];

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {/* Create Artifact Section */}
      <div className="rounded-lg bg-white p-6 shadow">
        <h2 className="mb-4 text-xl font-semibold text-gray-900">Create Artifact</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {artifactTypes.map((type) => (
            <button
              key={type.id}
              onClick={() => setCreateType(type.id)}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              {type.label}
            </button>
          ))}
        </div>
      </div>

      {/* Artifacts List */}
      <div className="rounded-lg bg-white shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Artifacts</h2>
            {loading && (
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent"></div>
                <span>Loading...</span>
              </div>
            )}
          </div>
        </div>
        {loading && artifacts.length === 0 ? (
          <div className="p-6 text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"></div>
            <p className="mt-4 text-gray-600">Loading artifacts...</p>
          </div>
        ) : artifacts.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No artifacts created yet. Create an artifact to get started.
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {artifacts.map((artifact, idx) => (
              <li key={idx} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-sm font-medium text-gray-900">
                        {artifact.name || `Artifact ${idx + 1}`}
                      </h3>
                      {artifact.type && (
                        <span className="text-xs text-gray-500">({artifact.type})</span>
                      )}
                      <span
                        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(
                          artifact.status,
                          artifact.is_generating
                        )}`}
                      >
                        {artifact.is_generating ? 'Generating...' : artifact.status}
                      </span>
                    </div>
                    {artifact.details && (
                      <p className="mt-1 text-xs text-gray-500">{artifact.details}</p>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    {artifact.has_play && (
                      <button
                        className="rounded-md bg-indigo-600 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 flex items-center space-x-1"
                        onClick={() => handleDownload(artifact.name || '')}
                        disabled={downloading === artifact.name}
                      >
                        {downloading === artifact.name ? (
                          <>
                            <div className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-solid border-white border-r-transparent"></div>
                            <span>Downloading...</span>
                          </>
                        ) : (
                          <span>Play</span>
                        )}
                      </button>
                    )}
                    {artifact.status === 'ready' && (
                      <button
                        onClick={() => handleDownload(artifact.name || '')}
                        className="rounded-md bg-indigo-600 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 flex items-center space-x-1"
                        disabled={downloading === artifact.name}
                      >
                        {downloading === artifact.name ? (
                          <>
                            <div className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-solid border-white border-r-transparent"></div>
                            <span>Downloading...</span>
                          </>
                        ) : (
                          <span>Download</span>
                        )}
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(artifact.name || '')}
                      disabled={deleting === artifact.name}
                      className="rounded-md bg-red-600 px-3 py-1 text-xs font-semibold text-white hover:bg-red-500 disabled:opacity-50"
                    >
                      {deleting === artifact.name ? 'Deleting...' : 'Delete'}
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {createType && (
        <ArtifactCreateModal
          notebookId={notebookId}
          artifactType={createType}
          onClose={() => {
            setCreateType(null);
            onArtifactsChange();
          }}
        />
      )}
    </div>
  );
}

