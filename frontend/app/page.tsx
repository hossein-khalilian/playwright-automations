import { redirect } from 'next/navigation';
import { routing } from '@/i18n/config';

export default function RootPage() {
  redirect(`/${routing.defaultLocale}`);
}

