import { NavLink } from 'react-router'
import { useTranslation } from 'react-i18next'
import { Leaf } from 'lucide-react'
import { LanguageToggle } from '@/components/language-toggle'
import { MobileNav } from '@/components/mobile-nav'
import { ThemeToggle } from '@/components/theme-toggle'
import { useVisualViewport } from '@/hooks/use-visual-viewport'
import { NAV_ITEMS } from '@/lib/nav'
import { cn } from '@/lib/utils'

export function AppShell({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation()
  useVisualViewport()

  return (
    <div
      className="app-viewport bg-background flex flex-col overflow-hidden"
      style={{ height: 'var(--app-height, 100dvh)' }}
    >
      <header className="bg-background/90 z-10 border-b backdrop-blur">
        <div className="mx-auto flex h-12 w-full max-w-5xl items-center justify-between gap-4 px-3 sm:h-14 sm:px-4">
          <NavLink to="/" end className="flex items-center gap-2 font-semibold">
            <Leaf className="text-primary size-5" />
            <span className="hidden sm:inline">{t('common.appTitle')}</span>
            <span className="sm:hidden">{t('common.appTitleShort')}</span>
          </NavLink>
          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map(({ to, labelKey, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  cn(
                    'hidden items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors sm:flex',
                    isActive
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
                  )
                }
              >
                <Icon className="size-4" />
                <span>{t(labelKey)}</span>
              </NavLink>
            ))}
            <LanguageToggle />
            <ThemeToggle />
          </nav>
        </div>
      </header>
      <main className="mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col overflow-hidden py-3 sm:py-6">
        {children}
      </main>
      <MobileNav />
      <footer className="hidden border-t py-4 sm:block">
        <p className="text-muted-foreground mx-auto w-full max-w-5xl px-4 text-xs">
          {t('common.footer')}
        </p>
      </footer>
    </div>
  )
}
