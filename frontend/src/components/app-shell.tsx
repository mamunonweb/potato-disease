import type { ComponentType } from 'react'
import { NavLink } from 'react-router'
import { useTranslation } from 'react-i18next'
import {
  BarChart3,
  BookOpen,
  Layers,
  Leaf,
  MessageCircle,
  ScanSearch,
} from 'lucide-react'
import { LanguageToggle } from '@/components/language-toggle'
import { ThemeToggle } from '@/components/theme-toggle'
import { cn } from '@/lib/utils'

interface NavItem {
  to: string
  labelKey: string
  icon: ComponentType<{ className?: string }>
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', labelKey: 'nav.detect', icon: ScanSearch },
  { to: '/results', labelKey: 'nav.results', icon: BarChart3 },
  { to: '/batch', labelKey: 'nav.batch', icon: Layers },
  { to: '/chat', labelKey: 'nav.chat', icon: MessageCircle },
  { to: '/info', labelKey: 'nav.info', icon: BookOpen },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation()

  return (
    <div className="bg-background flex h-svh flex-col overflow-hidden">
      <header className="bg-background/90 sticky top-0 z-10 border-b backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between gap-4 px-4">
          <NavLink to="/" className="flex items-center gap-2 font-semibold">
            <Leaf className="text-primary size-5" />
            <span className="hidden sm:inline">{t('common.appTitle')}</span>
            <span className="sm:hidden">{t('common.appTitleShort')}</span>
          </NavLink>
          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map(({ to, labelKey, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
                  )
                }
              >
                <Icon className="size-4" />
                <span className="hidden sm:inline">{t(labelKey)}</span>
              </NavLink>
            ))}
            <LanguageToggle />
            <ThemeToggle />
          </nav>
        </div>
      </header>
      <main className="mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col overflow-y-auto px-4 py-6">
        {children}
      </main>
      <footer className="border-t py-4">
        <p className="text-muted-foreground mx-auto w-full max-w-5xl px-4 text-xs">
          {t('common.footer')}
        </p>
      </footer>
    </div>
  )
}
