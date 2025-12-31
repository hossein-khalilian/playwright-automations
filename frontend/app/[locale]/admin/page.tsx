'use client';

import { useEffect, useState } from 'react';
import { useRouter } from '@/lib/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslations, useLocale } from 'next-intl';
import { adminApi, authApi } from '@/lib/api-client';
import type { GoogleCredential } from '@/lib/types';
import Navbar from '@/components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2, Shield, CheckCircle2, XCircle, Plus, Trash2, Mail, Pencil, RefreshCw, AlertCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

export default function AdminDashboardPage() {
  const { isAuthenticated, isAdmin, loading: authLoading } = useAuth();
  const router = useRouter();
  const locale = useLocale();
  const isRTL = locale === 'fa';
  const t = useTranslations('admin');
  const tCommon = useTranslations('common');
  const [testResult, setTestResult] = useState<{ message: string; username: string; roles: string[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [credentials, setCredentials] = useState<GoogleCredential[]>([]);
  const [loadingCredentials, setLoadingCredentials] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [creating, setCreating] = useState(false);
  const [deletingEmail, setDeletingEmail] = useState<string | null>(null);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingEmail, setEditingEmail] = useState<string | null>(null);
  const [editPassword, setEditPassword] = useState('');
  const [updating, setUpdating] = useState(false);
  const [checkingEmail, setCheckingEmail] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }

    if (!authLoading && !isAdmin) {
      router.push('/notebooks');
      return;
    }

    if (isAdmin) {
      loadCredentials();
    }
  }, [isAuthenticated, isAdmin, authLoading, router]);

  const loadCredentials = async () => {
    try {
      setLoadingCredentials(true);
      const response = await adminApi.listGoogleCredentials();
      setCredentials(response.credentials);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('loadCredentialsFailed'));
    } finally {
      setLoadingCredentials(false);
    }
  };

  const handleTestAdmin = async () => {
    setLoading(true);
    setError('');
    setTestResult(null);

    try {
      const result = await authApi.adminTest();
      setTestResult(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('testFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleAddCredential = async () => {
    if (!newEmail || !newPassword) {
      setError(t('emailPasswordRequired'));
      return;
    }

    setCreating(true);
    setError('');

    try {
      await adminApi.createGoogleCredential({
        email: newEmail,
        password: newPassword,
      });
      setShowAddDialog(false);
      setNewEmail('');
      setNewPassword('');
      await loadCredentials();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('createCredentialFailed'));
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteCredential = async (email: string) => {
    if (!confirm(t('deleteConfirm', { email }))) {
      return;
    }

    setDeletingEmail(email);
    setError('');

    try {
      await adminApi.deleteGoogleCredential(email);
      await loadCredentials();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('deleteCredentialFailed'));
    } finally {
      setDeletingEmail(null);
    }
  };

  const handleStartEdit = (email: string) => {
    setEditingEmail(email);
    setEditPassword('');
    setShowEditDialog(true);
    setError('');
  };

  const handleUpdateCredential = async () => {
    if (!editingEmail || !editPassword) {
      setError(t('passwordRequired'));
      return;
    }

    if (editPassword.length < 6) {
      setError(t('passwordMinLength'));
      return;
    }

    setUpdating(true);
    setError('');

    try {
      await adminApi.updateGoogleCredential(editingEmail, {
        password: editPassword,
      });
      setShowEditDialog(false);
      setEditingEmail(null);
      setEditPassword('');
      await loadCredentials();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('updateCredentialFailed'));
    } finally {
      setUpdating(false);
    }
  };

  const handleCheckCredential = async (email: string) => {
    setCheckingEmail(email);
    setError('');

    try {
      // Submit the check task
      const submission = await adminApi.checkGoogleCredential(email);
      
      if (!submission.task_id) {
        throw new Error('Task submission did not return a task_id');
      }

      // Poll for task status
      const pollInterval = 2000; // Poll every 2 seconds
      const maxAttempts = 30; // Maximum 60 seconds
      
      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        await new Promise(resolve => setTimeout(resolve, pollInterval));
        
        try {
          const status = await adminApi.getGoogleCredentialCheckStatus(submission.task_id);
          
          if (status.status === 'success') {
            // Task completed successfully
            await loadCredentials(); // Reload to get updated status
            setError(''); // Clear any previous errors
            break;
          } else if (status.status === 'failure') {
            // Task failed
            setError(status.message || t('checkCredentialFailed'));
            await loadCredentials(); // Reload to get updated status
            break;
          }
          // If still pending, continue polling
        } catch (pollErr: any) {
          // If polling fails, log but continue
          console.warn('Error polling credential check status:', pollErr);
          if (attempt === maxAttempts - 1) {
            setError(t('checkCredentialFailed'));
          }
        }
      }
      
      // Final reload to ensure we have the latest status
      await loadCredentials();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || t('checkCredentialFailed'));
    } finally {
      setCheckingEmail(null);
    }
  };

  const getStatusBadge = (cred: GoogleCredential) => {
    const status = cred.status || 'unknown';
    const isChecking = checkingEmail === cred.email;
    
    if (isChecking) {
      return (
        <span className="inline-flex items-center gap-1 text-sm text-blue-600">
          <Loader2 className="h-3 w-3 animate-spin" />
          {t('checking')}
        </span>
      );
    }

    switch (status) {
      case 'working':
        return (
          <span className="inline-flex items-center gap-1 text-sm text-green-600">
            <CheckCircle2 className="h-3 w-3" />
            {t('working')}
          </span>
        );
      case 'not_working':
        return (
          <span className="inline-flex items-center gap-1 text-sm text-red-600">
            <XCircle className="h-3 w-3" />
            {t('notWorking')}
          </span>
        );
      case 'checking':
        return (
          <span className="inline-flex items-center gap-1 text-sm text-blue-600">
            <Loader2 className="h-3 w-3 animate-spin" />
            {t('checking')}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-sm text-gray-600">
            <AlertCircle className="h-3 w-3" />
            {t('unknown')}
          </span>
        );
    }
  };

  if (authLoading || !isAuthenticated || !isAdmin) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-background">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-foreground flex items-center gap-2">
              <Shield className="h-8 w-8" />
              {t('title')}
            </h1>
            <p className="mt-2 text-muted-foreground">{t('description')}</p>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>{t('adminTest')}</CardTitle>
                <CardDescription>{t('adminTestDescription')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={handleTestAdmin}
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Loader2 className={`h-4 w-4 ${isRTL ? 'ml-2' : 'mr-2'} animate-spin`} />
                      {t('testing')}
                    </>
                  ) : (
                    t('testAdminAccess')
                  )}
                </Button>

                {testResult && (
                  <Alert>
                    <div className="flex items-start gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5" />
                      <div className="flex-1">
                        <AlertDescription className="font-semibold mb-1">
                          {testResult.message}
                        </AlertDescription>
                        <div className="text-sm text-muted-foreground space-y-1">
                          <p>{t('username')}: {testResult.username}</p>
                          <p>{t('role')}: {testResult.roles.join(', ')}</p>
                        </div>
                      </div>
                    </div>
                  </Alert>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t('systemInfo')}</CardTitle>
                <CardDescription>{t('systemInfoDescription')}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">{t('adminAccess')}:</span>
                    <span className="font-medium flex items-center gap-1">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      {t('enabled')}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">{t('roleBasedAccess')}:</span>
                    <span className="font-medium flex items-center gap-1">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      {t('active')}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t('quickActions')}</CardTitle>
                <CardDescription>{t('quickActionsDescription')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => router.push('/notebooks')}
                >
                  {t('viewNotebooks')}
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => router.push('/')}
                >
                  {t('goHome')}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Google Credentials Management */}
          <Card className="mt-6">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Mail className="h-5 w-5" />
                    {t('googleCredentials')}
                  </CardTitle>
                  <CardDescription>{t('googleCredentialsDescription')}</CardDescription>
                </div>
                <Button onClick={() => setShowAddDialog(true)}>
                  <Plus className={`h-4 w-4 ${isRTL ? 'ml-2' : 'mr-2'}`} />
                  {t('addCredential')}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loadingCredentials ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : credentials.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  {t('noCredentials')}
                </div>
              ) : (
                <div className="space-y-2">
                  {credentials.map((cred) => (
                    <div
                      key={cred.email}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex-1">
                        <div className="font-medium flex items-center gap-2">
                          {cred.email}
                          {getStatusBadge(cred)}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {t('createdAt')}: {new Date(cred.created_at).toLocaleString()}
                          {!cred.is_active && (
                            <span className={`${isRTL ? 'mr-2' : 'ml-2'} text-orange-500`}>
                              ({t('inactive')})
                            </span>
                          )}
                          {cred.status_checked_at && (
                            <span className={`${isRTL ? 'mr-2' : 'ml-2'}`}>
                              • {t('lastChecked')}: {new Date(cred.status_checked_at).toLocaleString()}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className={`flex gap-2 ${isRTL ? 'flex-row-reverse' : ''}`}>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleCheckCredential(cred.email)}
                          disabled={checkingEmail === cred.email || deletingEmail === cred.email}
                          title={t('checkCredential')}
                        >
                          {checkingEmail === cred.email ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <RefreshCw className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleStartEdit(cred.email)}
                          disabled={deletingEmail === cred.email || checkingEmail === cred.email}
                          title={tCommon('edit')}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeleteCredential(cred.email)}
                          disabled={deletingEmail === cred.email || checkingEmail === cred.email}
                          title={tCommon('delete')}
                        >
                          {deletingEmail === cred.email ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Add Credential Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('addCredential')}</DialogTitle>
            <DialogDescription>{t('addCredentialDescription')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="email">{t('email')}</Label>
              <Input
                id="email"
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder={t('emailPlaceholder')}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">{t('password')}</Label>
              <Input
                id="password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder={t('passwordPlaceholder')}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDialog(false)}>
              {tCommon('cancel')}
            </Button>
            <Button onClick={handleAddCredential} disabled={creating}>
              {creating ? (
                <>
                  <Loader2 className={`h-4 w-4 ${isRTL ? 'ml-2' : 'mr-2'} animate-spin`} />
                  {t('creating')}
                </>
              ) : (
                tCommon('create')
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Credential Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('editCredential')}</DialogTitle>
            <DialogDescription>{t('editCredentialDescription', { email: editingEmail || '' })}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-email">{t('email')}</Label>
              <Input
                id="edit-email"
                type="email"
                value={editingEmail || ''}
                disabled
                className="bg-muted"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-password">{t('password')}</Label>
              <Input
                id="edit-password"
                type="password"
                value={editPassword}
                onChange={(e) => setEditPassword(e.target.value)}
                placeholder={t('passwordPlaceholder')}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              {tCommon('cancel')}
            </Button>
            <Button onClick={handleUpdateCredential} disabled={updating}>
              {updating ? (
                <>
                  <Loader2 className={`h-4 w-4 ${isRTL ? 'ml-2' : 'mr-2'} animate-spin`} />
                  {t('updating')}
                </>
              ) : (
                tCommon('update')
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

