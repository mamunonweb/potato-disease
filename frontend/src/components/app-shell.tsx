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
    <div className="flex min-h-svh flex-col bg-background">
      <header className="sticky top-0 z-10 border-b bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between gap-4 px-4">
          <NavLink to="/" className="flex items-center gap-2 font-semibold">
            <Leaf className="size-5 text-primary" />
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
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">{children}</main>
      <footer className="border-t py-4">
        <p className="mx-auto w-full max-w-5xl px-4 text-xs text-muted-foreground">
          AI-based preliminary classification — not a definitive diagnosis.
          For serious or rapidly spreading crop disease, consult a qualified
          agricultural professional.
        </p>
      </footer>
    </div>
  )
}
