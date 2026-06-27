import { useEffect, useState } from 'react'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { BridgeConsentQueue } from './BridgeConsentQueue'
import { LanguageSwitcher } from './i18n/LanguageSwitcher'
import { NotificationBell } from './NotificationBell'
import { UserMenu } from './UserMenu'
import { BrandLogo } from './brand/BrandLogo'
import { GardenBackdrop } from './garden/GardenBackdrop'
import { SecurityTrustStrip } from './trust/SecurityTrustStrip'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'

export function Layout() {
  const { user, token, logout, loading } = useAuth()
  const { tr } = useLocale()
  const navigate = useNavigate()
  const [balance, setBalance] = useState<number | null>(null)
  const [search, setSearch] = useState('')

  useEffect(() => {
    if (!token) {
      setBalance(null)
      return
    }
    api.getWallet(token)
      .then((w) => setBalance(Number(w.balance_usd)))
      .catch(() => setBalance(null))
  }, [token, user?.id])

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    const q = search.trim()
    navigate(q ? `/?q=${encodeURIComponent(q)}` : '/')
  }

  return (
    <div className="relative min-h-screen flex flex-col">
      <GardenBackdrop />
      <header className="sticky top-0 z-50 border-b border-[var(--color-border)]/70 bg-[var(--color-surface-raised)]/95 backdrop-blur-md">
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-[var(--color-market)]/35 to-transparent" />
        <div className="mx-auto flex h-[3.75rem] sm:h-[4.5rem] max-w-7xl items-center gap-2 px-3 sm:px-6">
          <BrandLogo variant="header" />

          <form onSubmit={handleSearch} className="flex-1 max-w-[260px] sm:max-w-xl ml-2">
            <div className="relative">
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={tr('searchPlaceholder')}
                className="w-full rounded-xl border border-[var(--color-border)] bg-white py-1.5 sm:py-2 pl-4 pr-9 text-sm font-medium text-[var(--color-text)] placeholder:text-[var(--color-muted)] focus:border-[var(--color-sage)] focus:outline-none focus:ring-2 focus:ring-[var(--color-sage)]/30"
              />
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-muted)]">⌕</span>
            </div>
          </form>

          <nav className="ml-auto flex items-center gap-1 sm:gap-1.5 text-sm">
            <LanguageSwitcher compact />
            {user ? (
              <>
                <Link
                  to="/garden"
                  className="rounded-xl bg-[var(--color-market)] px-3.5 py-1.5 sm:py-2 text-xs sm:text-sm font-bold text-white shadow-sm hover:bg-[var(--color-market-hover)] active:scale-[0.985] md:bg-transparent md:font-semibold md:text-[var(--color-market-hover)] md:shadow-none md:hover:bg-[var(--color-surface-overlay)]"
                >
                  <span className="md:hidden">{tr('navCreate')}</span>
                  <span className="hidden md:inline">{tr('navGarden')}</span>
                </Link>
                <Link
                  to="/community"
                  className="hidden md:inline rounded-lg px-2.5 py-1.5 text-sm font-medium text-[var(--color-text-soft)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-overlay)]"
                >
                  {tr('navCommunity')}
                </Link>
                <Link
                  to="/creator"
                  className="hidden sm:inline rounded-lg px-2.5 py-1.5 text-sm font-medium text-[var(--color-text-soft)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-overlay)]"
                >
                  {tr('navStore')}
                </Link>
                {token && <NotificationBell token={token} />}
                <UserMenu user={user} balance={balance} onLogout={logout} />
              </>
            ) : !loading ? (
              <>
                <Link
                  to="/garden"
                  className="rounded-xl bg-[var(--color-market)] px-3 py-1.5 sm:py-2 text-xs sm:text-sm font-bold text-white shadow-sm hover:bg-[var(--color-market-hover)] active:scale-[0.985] sm:bg-transparent sm:font-semibold sm:text-[var(--color-market-hover)] sm:shadow-none sm:hover:bg-[var(--color-surface-overlay)]"
                >
                  <span className="sm:hidden">{tr('navCreate')}</span>
                  <span className="hidden sm:inline">{tr('navGarden')}</span>
                </Link>
                <Link
                  to="/login"
                  className="rounded-lg px-2.5 py-1.5 text-sm font-medium text-[var(--color-text-soft)] hover:text-[var(--color-text)]"
                >
                  {tr('navLogin')}
                </Link>
                <Link
                  to="/register"
                  className="rounded-xl bg-[var(--color-market)] px-3.5 py-1.5 sm:py-2 text-xs sm:text-sm font-bold text-white shadow-sm hover:bg-[var(--color-market-hover)]"
                >
                  {tr('navRegister')}
                </Link>
              </>
            ) : null}
          </nav>
        </div>
      </header>

      <main className="relative z-10 flex-1 pb-6 sm:pb-0">
        <Outlet />
      </main>

      <BridgeConsentQueue />

      <footer className="relative z-10 border-t border-[var(--color-border)]/60 coffee-corner py-6 sm:py-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <p className="text-center text-xs font-semibold text-[var(--color-coffee)]">
            {tr('footerCoffee')}
          </p>
          <SecurityTrustStrip compact />
          <nav className="mt-6 flex flex-wrap justify-center gap-x-5 gap-y-2 text-xs font-medium text-[var(--color-text-soft)]">
            <Link to="/garden" className="hover:text-[var(--color-text)]">{tr('footerGarden')}</Link>
            <Link to="/smart-farm" className="hover:text-[var(--color-text)]">{tr('navSmartFarm')}</Link>
            <Link to="/community" className="hover:text-[var(--color-text)]">{tr('footerCommunity')}</Link>
            <Link to="/pricing" className="hover:text-[var(--color-text)]">{tr('footerPricing')}</Link>
            <Link to="/terms" className="hover:text-[var(--color-text)]">{tr('footerTerms')}</Link>
            <Link to="/security" className="hover:text-[var(--color-text)]">{tr('footerSecurity')}</Link>
            <Link to="/privacy" className="hover:text-[var(--color-text)]">{tr('footerPrivacy')}</Link>
            <Link to="/refunds" className="hover:text-[var(--color-text)]">{tr('footerRefunds')}</Link>
          </nav>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <BrandLogo variant="footer" linked={false} />
            <p className="text-xs font-medium text-[var(--color-text-soft)]">{tr('footerTagline')}</p>
          </div>
        </div>
      </footer>
    </div>
  )
}