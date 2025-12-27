'use client';

import { Link, useRouter } from '@/lib/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslations, useLocale } from 'next-intl';
import TaskStatusPanel from './TaskStatusPanel';
import LanguageSwitcher from './LanguageSwitcher';
import { Button } from '@/components/ui/button';

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const router = useRouter();
  const locale = useLocale();
  const isRTL = locale === 'fa';
  const t = useTranslations('navbar');
  const tAuth = useTranslations('auth');

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <nav className="border-b bg-background shadow-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 justify-between">
          <div className="flex">
            <Link
              href="/notebooks"
              className="inline-flex items-center border-b-2 border-primary px-1 pt-1 text-sm font-medium text-foreground transition-colors hover:text-primary"
            >
              {t('notebooks')}
            </Link>
          </div>
          <div className={`flex items-center gap-4 ${isRTL ? 'flex-row-reverse' : ''}`}>
            {isRTL ? (
              <>
                <Button
                  onClick={handleLogout}
                  variant="default"
                  size="sm"
                >
                  {tAuth('logout')}
                </Button>
                <span className="text-sm text-muted-foreground">{t('welcomeUser', { user: user || '' })}</span>
                <LanguageSwitcher />
                <TaskStatusPanel />
              </>
            ) : (
              <>
                <TaskStatusPanel />
                <LanguageSwitcher />
                <span className="text-sm text-muted-foreground">{t('welcomeUser', { user: user || '' })}</span>
                <Button
                  onClick={handleLogout}
                  variant="default"
                  size="sm"
                >
                  {tAuth('logout')}
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

