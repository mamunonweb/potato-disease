import type { ComponentType } from 'react'
import { NavLink } from 'react-router'
import {
  BarChart3,
  BookOpen,
  Layers,
  Leaf,
  MessageCircle,
  ScanSearch,
} from 'lucide-react'
import { ThemeToggle } from '@/components/theme-toggle'
import { cn } from '@/lib/utils'

interface NavItem {
  to: string
  label: string
  icon: ComponentType<{ className?: string }>
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Detect', icon: ScanSearch },
  { to: '/results', label: 'Results', icon: BarChart3 },
  { to: '/batch', label: 'Batch', icon: Layers },
  { to: '/chat', label: 'Chat', icon: MessageCircle },
  { to: '/info', label: 'Info', icon: BookOpen },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-background flex min-h-svh flex-col">
      <header className="bg-background/90 sticky top-0 z-10 border-b backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between gap-4 px-4">
          <NavLink to="/" className="flex items-center gap-2 font-semibold">
            <Leaf className="text-primary size-5" />
            <span className="hidden sm:inline">Potato Disease Detection</span>
            <span className="sm:hidden">Potato</span>
          </NavLink>
          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
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
                <span className="hidden sm:inline">{label}</span>
              </NavLink>
            ))}
            <ThemeToggle />
          </nav>
        </div>
      </header>
      <main className="mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col px-4 py-6">
        {children}
      </main>
      <footer className="border-t py-4">
        <p className="text-muted-foreground mx-auto w-full max-w-5xl px-4 text-xs">
          AI-based preliminary classification — not a definitive diagnosis.
        </p>
      </footer>
    </div>
  )
}
