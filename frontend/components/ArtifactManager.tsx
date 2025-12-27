'use client';

import { useState } from 'react';
import { artifactApi } from '@/lib/api-client';
import type { ArtifactInfo } from '@/lib/types';
import ArtifactCreateModal from './ArtifactCreateModal';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, RefreshCw, Trash2, Download } from 'lucide-react';

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
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {info && !error && (
        <Alert>
          <AlertDescription>{info}</AlertDescription>
        </Alert>
      )}

      {/* Create Artifact Section */}
      <Card>
        <CardHeader>
          <CardTitle>Create Artifact</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {artifactTypes.map((type) => (
              <Button
                key={type.id}
                onClick={() => setCreateType(type.id)}
                variant="outline"
              >
                {type.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Artifacts List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Artifacts</CardTitle>
            <div className="flex items-center space-x-2">
              {loading && (
                <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Loading...</span>
                </div>
              )}
              <Button
                onClick={onArtifactsChange}
                disabled={loading}
                variant="outline"
                size="sm"
                title="Reload artifacts"
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                Reload
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading && artifacts.length === 0 ? (
            <div className="text-center py-8">
              <Loader2 className="inline-block h-8 w-8 animate-spin" />
              <p className="mt-4 text-muted-foreground">Loading artifacts...</p>
            </div>
          ) : artifacts.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              No artifacts created yet. Create an artifact to get started.
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {artifacts.map((artifact, idx) => (
                <li key={idx} className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-sm font-medium text-foreground">
                          {artifact.name || `Artifact ${idx + 1}`}
                        </h3>
                        {artifact.type && (
                          <span className="text-xs text-muted-foreground">({artifact.type})</span>
                        )}
                        <Badge
                          variant={
                            artifact.is_generating
                              ? 'secondary'
                              : artifact.status === 'ready'
                              ? 'default'
                              : 'outline'
                          }
                        >
                          {artifact.is_generating ? 'Generating...' : artifact.status}
                        </Badge>
                      </div>
                      {artifact.details && (
                        <p className="mt-1 text-xs text-muted-foreground">{artifact.details}</p>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      {/* Show download button for ready artifacts, mindmaps, infographics, flashcards, slide decks, and reports */}
                      {/* Note: Play button removed for audio/video - they use download instead */}
                      {(artifact.status === 'ready' || artifact.type === 'mind_map' || artifact.type === 'infographic' || artifact.type === 'flashcards' || artifact.type === 'slide_deck' || artifact.type === 'reports') && (
                        <Button
                          onClick={() => handleDownload(artifact.name || '')}
                          disabled={downloading === artifact.name}
                          size="sm"
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
                              : artifact.type === 'reports'
                              ? 'Download report'
                              : 'Download artifact'
                          }
                        >
                          {downloading === artifact.name ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                              Downloading...
                            </>
                          ) : (
                            <>
                              <Download className="h-4 w-4 mr-1" />
                              Download
                            </>
                          )}
                        </Button>
                      )}
                      <Button
                        onClick={() => handleDelete(artifact.name || '')}
                        disabled={deleting === artifact.name}
                        variant="destructive"
                        size="icon"
                        title="Delete"
                      >
                        {deleting === artifact.name ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

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

