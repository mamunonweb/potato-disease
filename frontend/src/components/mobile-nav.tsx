import { NavLink } from 'react-router'
import { useTranslation } from 'react-i18next'
import { NAV_ITEMS } from '@/lib/nav'
import { cn } from '@/lib/utils'

export function MobileNav() {
  const { t } = useTranslation()

  return (
    <nav className="bg-background/95 shrink-0 border-t pb-[env(safe-area-inset-bottom)] backdrop-blur sm:hidden">
      <div className="grid grid-cols-5">
        {NAV_ITEMS.map(({ to, labelKey, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex flex-col items-center gap-0.5 py-2 text-[11px] font-medium transition-colors',
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground',
              )
            }
          >
            <Icon className="size-5" />
            <span>{t(labelKey)}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
