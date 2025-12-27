'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import TaskStatusPanel from './TaskStatusPanel';
import { Button } from '@/components/ui/button';

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const router = useRouter();

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
              Notebooks
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            <TaskStatusPanel />
            <span className="text-sm text-muted-foreground">Welcome, {user}</span>
            <Button
              onClick={handleLogout}
              variant="default"
              size="sm"
            >
              Logout
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}

