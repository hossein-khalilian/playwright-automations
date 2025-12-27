'use client';

import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
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
  const locale = useLocale();
  const isRTL = locale === 'fa';
  const t = useTranslations('artifacts');
  const tCommon = useTranslations('common');
  const [deleting, setDeleting] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [createType, setCreateType] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  const handleDelete = async (artifactName: string) => {
    if (!confirm(t('deleteConfirm', { name: artifactName }))) {
      return;
    }

    try {
      setDeleting(artifactName);
      setError('');
      setInfo('');
      const status = await artifactApi.delete(notebookId, artifactName);
      setInfo(status.message || t('deleteSubmitted'));
      await onArtifactsChange();
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || t('deleteFailed');
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
      setInfo(t('downloadCompleted'));
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || t('downloadFailed');
      setError(errorMessage);
      console.error('Download error:', err);
    } finally {
      setDownloading(null);
    }
  };

  const artifactTypes = [
    { id: 'audio-overview', label: t('audioOverview') },
    { id: 'video-overview', label: t('videoOverview') },
    { id: 'flashcards', label: t('flashcards') },
    { id: 'quiz', label: t('quiz') },
    { id: 'infographic', label: t('infographic') },
    { id: 'slide-deck', label: t('slideDeck') },
    { id: 'report', label: t('report') },
    { id: 'mindmap', label: t('mindMap') },
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
          <CardTitle dir={isRTL ? 'rtl' : 'ltr'}>{t('createArtifact')}</CardTitle>
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
          <div className={`flex items-center ${isRTL ? 'flex-row-reverse' : ''} justify-between`}>
            <CardTitle dir={isRTL ? 'rtl' : 'ltr'}>{t('title')}</CardTitle>
            <div className={`flex items-center ${isRTL ? 'space-x-reverse space-x-2' : 'space-x-2'}`}>
              {loading ? (
                <div className={`flex items-center ${isRTL ? 'space-x-reverse space-x-2 flex-row-reverse' : 'space-x-2'} text-sm text-muted-foreground`}>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span dir="auto">{tCommon('loading')}</span>
                </div>
              ) : (
                <Button
                  onClick={onArtifactsChange}
                  disabled={loading}
                  variant="outline"
                  size="sm"
                  title={t('reloadTitle')}
                >
                  <RefreshCw className={`h-4 w-4 ${isRTL ? 'ml-1' : 'mr-1'}`} />
                  {t('reload')}
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading && artifacts.length === 0 ? (
            <div className="text-center py-8">
              <Loader2 className="inline-block h-8 w-8 animate-spin" />
              <p className="mt-4 text-center text-muted-foreground" dir="auto">{t('loadingArtifacts')}</p>
            </div>
          ) : artifacts.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              <span className="text-center" dir="auto">{t('noArtifacts')}</span>
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {artifacts.map((artifact, idx) => (
                <li key={idx} className="py-4">
                  <div className={`flex items-center ${isRTL ? 'flex-row-reverse' : ''} justify-between`}>
                    <div className={`flex-1 ${isRTL ? 'text-right' : ''}`}>
                      <div className={`flex items-center ${isRTL ? 'space-x-3 justify-end' : 'space-x-3'}`}>
                        <h3 className="text-sm font-medium text-foreground" dir="auto">
                          {artifact.name || t('artifactLabel', { index: idx + 1 })}
                        </h3>
                        {artifact.type && (
                          <span className="text-xs text-muted-foreground" dir="auto">({artifact.type})</span>
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
                          <span dir="auto">{artifact.is_generating ? t('generating') : artifact.status}</span>
                        </Badge>
                      </div>
                      {artifact.details && (
                        <p className="mt-1 text-xs text-muted-foreground" dir="auto">{artifact.details}</p>
                      )}
                    </div>
                    <div className={`flex items-center ${isRTL ? 'space-x-reverse space-x-2' : 'space-x-2'}`}>
                      {isRTL ? (
                        <>
                          <Button
                            onClick={() => handleDelete(artifact.name || '')}
                            disabled={deleting === artifact.name}
                            variant="destructive"
                            size="icon"
                            title={tCommon('delete')}
                          >
                            {deleting === artifact.name ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </Button>
                          {/* Show download button for ready artifacts, mindmaps, infographics, flashcards, slide decks, and reports */}
                          {/* Note: Play button removed for audio/video - they use download instead */}
                          {(artifact.status === 'ready' || artifact.type === 'mind_map' || artifact.type === 'infographic' || artifact.type === 'flashcards' || artifact.type === 'slide_deck' || artifact.type === 'reports') && (
                            <Button
                              onClick={() => handleDownload(artifact.name || '')}
                              disabled={downloading === artifact.name}
                              size="sm"
                              title={
                                artifact.type === 'mind_map'
                                  ? t('downloadMindmap')
                                  : artifact.type === 'video_overview'
                                  ? t('downloadVideo')
                                  : artifact.type === 'audio_overview'
                                  ? t('downloadAudio')
                                  : artifact.type === 'infographic'
                                  ? t('downloadInfographic')
                                  : artifact.type === 'flashcards'
                                  ? t('downloadFlashcards')
                                  : artifact.type === 'slide_deck'
                                  ? t('downloadSlideDeck')
                                  : artifact.type === 'reports'
                                  ? t('downloadReport')
                                  : t('downloadArtifact')
                              }
                            >
                              {downloading === artifact.name ? (
                                <>
                                  <Loader2 className={`h-4 w-4 ${isRTL ? 'ml-1' : 'mr-1'} animate-spin`} />
                                  {t('downloading')}
                                </>
                              ) : (
                                <>
                                  <Download className={`h-4 w-4 ${isRTL ? 'ml-1' : 'mr-1'}`} />
                                  {t('download')}
                                </>
                              )}
                            </Button>
                          )}
                        </>
                      ) : (
                        <>
                          {/* Show download button for ready artifacts, mindmaps, infographics, flashcards, slide decks, and reports */}
                          {/* Note: Play button removed for audio/video - they use download instead */}
                          {(artifact.status === 'ready' || artifact.type === 'mind_map' || artifact.type === 'infographic' || artifact.type === 'flashcards' || artifact.type === 'slide_deck' || artifact.type === 'reports') && (
                            <Button
                              onClick={() => handleDownload(artifact.name || '')}
                              disabled={downloading === artifact.name}
                              size="sm"
                              title={
                                artifact.type === 'mind_map'
                                  ? t('downloadMindmap')
                                  : artifact.type === 'video_overview'
                                  ? t('downloadVideo')
                                  : artifact.type === 'audio_overview'
                                  ? t('downloadAudio')
                                  : artifact.type === 'infographic'
                                  ? t('downloadInfographic')
                                  : artifact.type === 'flashcards'
                                  ? t('downloadFlashcards')
                                  : artifact.type === 'slide_deck'
                                  ? t('downloadSlideDeck')
                                  : artifact.type === 'reports'
                                  ? t('downloadReport')
                                  : t('downloadArtifact')
                              }
                            >
                              {downloading === artifact.name ? (
                                <>
                                  <Loader2 className={`h-4 w-4 ${isRTL ? 'ml-1' : 'mr-1'} animate-spin`} />
                                  {t('downloading')}
                                </>
                              ) : (
                                <>
                                  <Download className={`h-4 w-4 ${isRTL ? 'ml-1' : 'mr-1'}`} />
                                  {t('download')}
                                </>
                              )}
                            </Button>
                          )}
                          <Button
                            onClick={() => handleDelete(artifact.name || '')}
                            disabled={deleting === artifact.name}
                            variant="destructive"
                            size="icon"
                            title={tCommon('delete')}
                          >
                            {deleting === artifact.name ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
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

