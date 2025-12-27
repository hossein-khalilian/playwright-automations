'use client';

import { useEffect } from 'react';
import { useRouter } from '@/lib/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslations } from 'next-intl';
import { Loader2 } from 'lucide-react';

export default function Home() {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const t = useTranslations('common');

  useEffect(() => {
    if (!loading) {
      if (isAuthenticated) {
        router.push('/notebooks');
      } else {
        router.push('/login');
      }
    }
  }, [isAuthenticated, loading, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <Loader2 className="inline-block h-8 w-8 animate-spin" />
        <p className="mt-4 text-muted-foreground">{t('loading')}</p>
      </div>
    </div>
  );
}

