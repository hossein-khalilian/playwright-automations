'use client';

import { useState, useRef } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { sourceApi } from '@/lib/api-client';
import type { Source } from '@/lib/types';
import SourceReviewModal from './SourceReviewModal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, RefreshCw, Trash2, FileEdit, Eye, Upload, X } from 'lucide-react';

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
  const locale = useLocale();
  const isRTL = locale === 'fa';
  const t = useTranslations('sources');
  const tCommon = useTranslations('common');
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
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  const handleFileSelect = (file: File) => {
    if (file) {
      setSelectedFile(file);
      setError('');
      setInfo('');
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
    e.target.value = ''; // Reset input to allow selecting the same file again
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (uploading) return;

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setError('');
      setInfo('');
      const status = await sourceApi.upload(notebookId, selectedFile);
      setInfo(status.message || t('uploadSubmitted'));
      setSelectedFile(null);
      // Small delay before reloading to allow processing
      await new Promise(resolve => setTimeout(resolve, 1000));
      // Reload sources after upload
      await onSourcesChange();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || t('uploadFailed');
      setError(errorMessage);
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleAddUrls = async () => {
    if (!urls.trim()) {
      setError(t('urlsRequired'));
      return;
    }

    try {
      setAddingUrls(true);
      setError('');
      setInfo('');
      const status = await sourceApi.addUrls(notebookId, urls.trim());
      setInfo(status.message || t('urlsSubmitted'));
      setUrls('');
      // Small delay before reloading to allow processing
      await new Promise(resolve => setTimeout(resolve, 1000));
      // Reload sources after adding URLs
      await onSourcesChange();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || t('addUrlsFailed');
      setError(errorMessage);
      console.error('Add URLs error:', err);
    } finally {
      setAddingUrls(false);
    }
  };

  const handleDelete = async (sourceName: string) => {
    if (!confirm(t('deleteConfirm', { name: sourceName }))) {
      return;
    }

    try {
      setDeleting(sourceName);
      setError('');
      setInfo('');
      const status = await sourceApi.delete(notebookId, sourceName);
      setInfo(status.message || t('deleteSubmitted'));
      await onSourcesChange();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || t('deleteFailed');
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
      setInfo(status.message || t('renameSubmitted'));
      setRenaming(null);
      setNewName('');
      await onSourcesChange();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || t('renameFailed');
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
          <CardTitle>{t('uploadSource')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            ref={fileInputRef}
            type="file"
            onChange={handleFileInputChange}
            disabled={uploading}
            className="hidden"
          />
          
          {!selectedFile ? (
            <div
              ref={dropZoneRef}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={handleBrowseClick}
              className={`
                relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12
                transition-colors cursor-pointer
                ${isDragging 
                  ? 'border-primary bg-primary/5' 
                  : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50'
                }
                ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <div className="flex flex-col items-center gap-4 text-center">
                <div className={`
                  rounded-full p-4
                  ${isDragging ? 'bg-primary/10' : 'bg-muted'}
                `}>
                  <Upload className={`h-8 w-8 ${isDragging ? 'text-primary' : 'text-muted-foreground'}`} />
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium">
                    {isDragging ? (
                      <span className="text-primary">{t('dropFile')}</span>
                    ) : (
                      <>
                        <span className="text-primary">{t('clickToUpload')}</span>
                        {' '}
                        {t('orDragDrop')}
                      </>
                    )}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {t('supportedFormats')}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className={`
              flex items-center gap-4 rounded-lg border bg-muted/50 p-4
              ${isRTL ? 'flex-row-reverse' : ''}
            `}>
              <div className="flex-shrink-0 rounded bg-background p-2">
                <Upload className="h-5 w-5 text-muted-foreground" />
              </div>
              <div className={`flex-1 min-w-0 ${isRTL ? 'text-right' : ''}`}>
                <p className="text-sm font-medium text-foreground truncate">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
              <div className={`flex items-center gap-2 ${isRTL ? 'flex-row-reverse' : ''}`}>
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                  }}
                  disabled={uploading}
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                >
                  <X className="h-4 w-4" />
                </Button>
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleFileUpload();
                  }}
                  disabled={uploading}
                  size="sm"
                >
                  {uploading ? (
                    <>
                      <Loader2 className={`h-4 w-4 ${isRTL ? 'ml-2' : 'mr-2'} animate-spin`} />
                      {t('uploading')}
                    </>
                  ) : (
                    <>
                      <Upload className={`h-4 w-4 ${isRTL ? 'ml-2' : 'mr-2'}`} />
                      {tCommon('upload')}
                    </>
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
          <CardTitle>{t('addUrlSources')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            placeholder={t('urlsPlaceholder')}
            disabled={addingUrls}
            rows={6}
            dir={isRTL ? 'rtl' : 'ltr'}
            className={isRTL ? 'text-right' : ''}
          />
          <div className="flex items-center justify-end">
            <Button
              onClick={handleAddUrls}
              disabled={addingUrls || !urls.trim()}
            >
              {addingUrls ? (
                <>
                  <Loader2 className={`h-4 w-4 ${isRTL ? 'ml-2' : 'mr-2'} animate-spin`} />
                  {t('adding')}
                </>
              ) : (
                t('addUrls')
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            {t('urlsHint')}
          </p>
        </CardContent>
      </Card>

      {/* Sources List */}
      <Card>
        <CardHeader>
          <div className={`flex items-center ${isRTL ? 'flex-row-reverse' : ''} justify-between`}>
            <CardTitle>{t('title')}</CardTitle>
            <div className={`flex items-center ${isRTL ? 'space-x-reverse space-x-2' : 'space-x-2'}`}>
              {loading && (
                <div className={`flex items-center ${isRTL ? 'space-x-reverse space-x-2' : 'space-x-2'} text-sm text-muted-foreground`}>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>{tCommon('loading')}</span>
                </div>
              )}
              <Button
                onClick={onSourcesChange}
                disabled={loading}
                variant="outline"
                size="sm"
                title={t('reloadTitle')}
              >
                <RefreshCw className={`h-4 w-4 ${isRTL ? 'ml-1' : 'mr-1'}`} />
                {t('reload')}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading && sources.length === 0 ? (
            <div className="text-center py-8">
              <Loader2 className="inline-block h-8 w-8 animate-spin" />
              <p className="mt-4 text-muted-foreground">{t('loadingSources')}</p>
            </div>
          ) : sources.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              {t('noSourcesSimple')}
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {sources.map((source) => (
                <li key={source.name} className="py-4">
                  <div className={`flex items-center ${isRTL ? 'flex-row-reverse' : ''} justify-between`}>
                    <div className={`flex-1 ${isRTL ? 'text-right' : ''}`}>
                      <div className={`flex items-center ${isRTL ? 'space-x-3 justify-end' : 'space-x-3'}`}>
                        {isRTL ? (
                          <>
                            <Badge
                              variant={
                                source.status === 'ready'
                                  ? 'default'
                                  : source.status === 'processing'
                                  ? 'secondary'
                                  : 'outline'
                              }
                            >
                              {source.status === 'ready'
                                ? t('statusReady')
                                : source.status === 'processing'
                                ? t('statusProcessing')
                                : t('statusUnknown')}
                            </Badge>
                            <h3 className="text-sm font-medium text-foreground">{source.name}</h3>
                          </>
                        ) : (
                          <>
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
                              {source.status === 'ready'
                                ? t('statusReady')
                                : source.status === 'processing'
                                ? t('statusProcessing')
                                : t('statusUnknown')}
                            </Badge>
                          </>
                        )}
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
                            placeholder={t('newName')}
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
                                <Loader2 className={`h-3 w-3 ${isRTL ? 'ml-1' : 'mr-1'} animate-spin`} />
                                {t('saving')}
                              </>
                            ) : (
                              tCommon('save')
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
                            {tCommon('cancel')}
                          </Button>
                        </div>
                      ) : (
                        <>
                          {isRTL ? (
                            <>
                              <Button
                                onClick={() => handleDelete(source.name)}
                                disabled={deleting === source.name}
                                variant="destructive"
                                size="icon"
                                title={tCommon('delete')}
                              >
                                {deleting === source.name ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Trash2 className="h-4 w-4" />
                                )}
                              </Button>
                              <Button
                                onClick={() => {
                                  setRenaming(source.name);
                                  setNewName(source.name);
                                }}
                                variant="outline"
                                size="sm"
                              >
                                <FileEdit className={`h-4 w-4 ${isRTL ? 'ml-1' : 'mr-1'}`} />
                                {t('rename')}
                              </Button>
                              <Button
                                onClick={() => setSelectedSource(source.name)}
                                size="sm"
                              >
                                <Eye className={`h-4 w-4 ${isRTL ? 'ml-1' : 'mr-1'}`} />
                                {t('review')}
                              </Button>
                            </>
                          ) : (
                            <>
                              <Button
                                onClick={() => setSelectedSource(source.name)}
                                size="sm"
                              >
                                <Eye className={`h-4 w-4 ${isRTL ? 'ml-1' : 'mr-1'}`} />
                                {t('review')}
                              </Button>
                              <Button
                                onClick={() => {
                                  setRenaming(source.name);
                                  setNewName(source.name);
                                }}
                                variant="outline"
                                size="sm"
                              >
                                <FileEdit className={`h-4 w-4 ${isRTL ? 'ml-1' : 'mr-1'}`} />
                                {t('rename')}
                              </Button>
                              <Button
                                onClick={() => handleDelete(source.name)}
                                disabled={deleting === source.name}
                                variant="destructive"
                                size="icon"
                                title={tCommon('delete')}
                              >
                                {deleting === source.name ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Trash2 className="h-4 w-4" />
                                )}
                              </Button>
                            </>
                          )}
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

