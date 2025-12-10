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
  const [info, setInfo] = useState('');

  const handleDelete = async (artifactName: string) => {
    if (!confirm(`Are you sure you want to delete "${artifactName}"?`)) {
      return;
    }

    try {
      setDeleting(artifactName);
      setError('');
      setInfo('');
      const status = await artifactApi.delete(notebookId, artifactName);
      setInfo(status.message || 'Delete submitted.');
      await onArtifactsChange();
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to delete artifact';
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
      setInfo('');
      await artifactApi.download(notebookId, artifactName);
      setInfo('Download completed successfully.');
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to download artifact';
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
      {info && !error && (
        <div className="rounded-md bg-blue-50 p-4">
          <div className="text-sm text-blue-800">{info}</div>
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
            <div className="flex items-center space-x-2">
              {loading && (
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent"></div>
                  <span>Loading...</span>
                </div>
              )}
              <button
                onClick={onArtifactsChange}
                disabled={loading}
                className="rounded-md bg-indigo-600 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 flex items-center space-x-1"
                title="Reload artifacts"
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
                    {/* Show download button for ready artifacts, mindmaps, infographics, flashcards, and slide decks */}
                    {/* Note: Play button removed for audio/video - they use download instead */}
                    {(artifact.status === 'ready' || artifact.type === 'mind_map' || artifact.type === 'infographic' || artifact.type === 'flashcards' || artifact.type === 'slide_deck') && (
                      <button
                        onClick={() => handleDownload(artifact.name || '')}
                        className="rounded-md bg-indigo-600 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 flex items-center space-x-1"
                        disabled={downloading === artifact.name}
                        title={
                          artifact.type === 'mind_map'
                            ? 'Download mindmap'
                            : artifact.type === 'video_overview'
                            ? 'Download video'
                            : artifact.type === 'audio_overview'
                            ? 'Download audio'
                            : artifact.type === 'infographic'
                            ? 'Download infographic'
                            : artifact.type === 'flashcards'
                            ? 'Download flashcards'
                            : artifact.type === 'slide_deck'
                            ? 'Download slide deck'
                            : 'Download artifact'
                        }
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

