import { Outlet } from 'react-router-dom'
import { BrandLogo } from './brand/BrandLogo'

/** Minimal layout for customer pairing — no login, no dashboard, no consent queue. */
export function CustomerJoinLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-[var(--color-surface)]">
      <header className="border-b border-[var(--color-border)] px-4 py-4 sm:px-6">
        <BrandLogo variant="header" linked={false} />
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="border-t border-[var(--color-border)] py-6 text-center text-xs text-[var(--color-muted)]">
        AgentNexus remote support · Customer pairing only
      </footer>
    </div>
  )
}