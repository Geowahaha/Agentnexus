import { useEffect, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import {
  fundingLabel,
  isPlatformTestTransaction,
  isTrialCreditTransaction,
  platformNoticeForTransaction,
  trialNoticeForTransaction,
} from '../lib/billingTrial'
import type { BillingConfig, BillingTransaction, EarningsSummary, Wallet } from '../types'

export function Billing() {
  const { token } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const [wallet, setWallet] = useState<Wallet | null>(null)
  const [config, setConfig] = useState<BillingConfig | null>(null)
  const [earnings, setEarnings] = useState<EarningsSummary | null>(null)
  const [transactions, setTransactions] = useState<BillingTransaction[]>([])
  const [amount, setAmount] = useState('10')
  const [loading, setLoading] = useState(true)
  const [toppingUp, setToppingUp] = useState(false)
  const [transferring, setTransferring] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  const stripeStatus = searchParams.get('stripe')

  function refresh() {
    if (!token) return
    Promise.all([
      api.getBillingConfig(),
      api.getWallet(token),
      api.getEarnings(token),
      api.listTransactions(token),
    ])
      .then(([cfg, w, e, txs]) => {
        setConfig(cfg)
        setWallet(w)
        setEarnings(e)
        setTransactions(txs)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load billing'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    refresh()
  }, [token])

  useEffect(() => {
    if (stripeStatus === 'success') {
      setNotice('Payment received. Your balance will update once Stripe confirms the payment.')
      setSearchParams({}, { replace: true })
      refresh()
    } else if (stripeStatus === 'cancel') {
      setNotice('Checkout cancelled. No charge was made.')
      setSearchParams({}, { replace: true })
    }
  }, [stripeStatus, setSearchParams])

  async function handleTopUp(e: FormEvent) {
    e.preventDefault()
    if (!token) return
    setToppingUp(true)
    setError('')
    setNotice('')
    try {
      if (config?.stripe_enabled) {
        const session = await api.createStripeCheckout(token, amount)
        window.location.href = session.checkout_url
        return
      }
      const updated = await api.topUp(token, amount)
      setWallet(updated)
      const txs = await api.listTransactions(token)
      setTransactions(txs)
      setNotice(`Added $${Number(amount).toFixed(2)} to your balance.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Top-up failed')
    } finally {
      setToppingUp(false)
    }
  }

  async function handleTransferEarnings() {
    if (!token) return
    setTransferring(true)
    setError('')
    setNotice('')
    try {
      const updated = await api.transferEarnings(token)
      setWallet(updated)
      const [e, txs] = await Promise.all([api.getEarnings(token), api.listTransactions(token)])
      setEarnings(e)
      setTransactions(txs)
      setNotice('Creator earnings moved to your spendable balance.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Transfer failed')
    } finally {
      setTransferring(false)
    }
  }

  if (loading) {
    return <div className="mx-auto max-w-3xl px-4 py-16 text-[var(--color-muted)]">Loading wallet…</div>
  }

  const balance = wallet ? Number(wallet.balance_usd) : 0
  const earningsBalance = earnings ? Number(earnings.earnings_balance_usd) : 0
  const totalEarned = earnings ? Number(earnings.total_earned_usd) : 0
  const platformFee = config?.platform_fee_percent ?? earnings?.platform_fee_percent ?? 20
  const signupCredits = config?.signup_credits_usd ?? 5

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold text-[var(--color-text)]">Billing</h1>
      <p className="mt-2 text-[var(--color-muted)]">
        Agent marketplace fees are charged per run. Creators earn {100 - platformFee}% of each agent fee
        from paid credits only; the platform keeps {platformFee}%.
      </p>

      <div className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 text-sm text-amber-950">
        <p className="font-semibold text-amber-900">
          เครดิตทดลองใช้ ${signupCredits.toFixed(0)} แรกเข้า — ใช้ซื้อได้ทุกอย่างใน marketplace
        </p>
        <p className="mt-1 text-amber-900/90">
          การทดลองใช้ (เครดิตแรกเข้า / demo) จะแสดงในบิลว่าเป็นการทดลองใช้ และ{' '}
          <strong>เจ้าของ agent ไม่ได้รับเงินจริง</strong> จากส่วนนี้ — ดู{' '}
          <Link to="/terms" className="font-semibold text-amber-950 underline hover:no-underline">
            ข้อตกลงการใช้งาน
          </Link>
        </p>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6">
          <p className="text-sm text-[var(--color-muted)]">Spendable balance</p>
          <p className="mt-1 font-mono text-4xl font-semibold text-cyan-400">${balance.toFixed(2)}</p>
          <p className="mt-2 text-xs text-[var(--color-muted)]">Used to run marketplace agents</p>
        </div>
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6">
          <p className="text-sm text-[var(--color-muted)]">Creator earnings</p>
          <p className="mt-1 font-mono text-4xl font-semibold text-emerald-400">${earningsBalance.toFixed(2)}</p>
          <p className="mt-2 text-xs text-[var(--color-muted)]">
            Lifetime earned: ${totalEarned.toFixed(2)}
          </p>
        </div>
      </div>

      <form onSubmit={handleTopUp} className="mt-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-6 space-y-4">
        <h2 className="font-semibold text-[var(--color-text)]">Add credits</h2>
        <p className="text-xs text-[var(--color-muted)]">
          {config?.stripe_enabled
            ? 'Pay securely with Stripe. Credits are added after payment confirmation.'
            : 'Demo top-up for local development (no real payment).'}
        </p>
        <div className="flex gap-3">
          <input
            type="number"
            step="0.01"
            min="0.01"
            max="100"
            required
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="flex-1 rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)] focus:border-cyan-500/50 focus:outline-none"
          />
          <button
            type="submit"
            disabled={toppingUp}
            className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-cyan-400 disabled:opacity-50"
          >
            {toppingUp
              ? config?.stripe_enabled
                ? 'Redirecting…'
                : 'Adding…'
              : config?.stripe_enabled
                ? 'Pay with Stripe'
                : 'Top up'}
          </button>
        </div>
        {notice && <p className="text-sm text-emerald-400">{notice}</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
      </form>

      {earningsBalance > 0 && (
        <div className="mt-6 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-6">
          <h2 className="font-semibold text-[var(--color-text)]">Transfer earnings</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Move creator earnings into your spendable balance to run more agents.
          </p>
          <button
            type="button"
            onClick={handleTransferEarnings}
            disabled={transferring}
            className="mt-4 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-emerald-400 disabled:opacity-50"
          >
            {transferring ? 'Transferring…' : `Transfer $${earningsBalance.toFixed(2)}`}
          </button>
        </div>
      )}

      {earnings && earnings.recent_earnings.length > 0 && (
        <section className="mt-10">
          <h2 className="text-lg font-semibold text-[var(--color-text)]">Creator payout history</h2>
          <ul className="mt-4 space-y-2">
            {earnings.recent_earnings.map((item) => (
              <li
                key={item.id}
                className="flex items-center justify-between rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-sm"
              >
                <div>
                  <p className="text-white">Agent run payout</p>
                  <p className="text-xs text-[var(--color-muted)]">
                    Gross ${Number(item.gross_amount_usd).toFixed(2)} · fee ${Number(item.platform_fee_usd).toFixed(2)} ·{' '}
                    {new Date(item.created_at).toLocaleString()}
                  </p>
                  <Link to={`/workflows/${item.workflow_id}`} className="text-xs text-cyan-400 hover:text-cyan-300">
                    View workflow
                  </Link>
                </div>
                <p className="font-mono text-emerald-400">+${Number(item.net_amount_usd).toFixed(4)}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-10">
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Transaction history</h2>
        {transactions.length === 0 ? (
          <p className="mt-4 text-sm text-[var(--color-muted)]">No transactions yet.</p>
        ) : (
          <ul className="mt-4 space-y-2">
            {transactions.map((tx) => {
              const trialNotice = trialNoticeForTransaction(tx)
              const platformNotice = platformNoticeForTransaction(tx)
              const funding = fundingLabel(tx.billing_meta)
              const platformBadge = isPlatformTestTransaction(tx) || funding === 'Platform tested'
              const trialBadge =
                !platformBadge && (isTrialCreditTransaction(tx) || funding === 'ทดลองใช้')
              return (
              <li
                key={tx.id}
                className="flex items-center justify-between rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-sm"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-white">{tx.description}</p>
                    {platformBadge && (
                      <span className="rounded-full bg-violet-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-violet-300">
                        Platform tested
                      </span>
                    )}
                    {trialBadge && (
                      <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-300">
                        ทดลองใช้
                      </span>
                    )}
                    {funding === 'ทดลอง + จ่ายจริง' && (
                      <span className="rounded-full bg-cyan-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-cyan-300">
                        ผสม
                      </span>
                    )}
                  </div>
                  {platformNotice && (
                    <p className="mt-1 text-xs font-medium text-violet-300/90">{platformNotice}</p>
                  )}
                  {trialNotice && (
                    <p className="mt-1 text-xs font-medium text-amber-300/90">{trialNotice}</p>
                  )}
                  <p className="mt-1 text-xs text-[var(--color-muted)]">
                    {tx.transaction_type.replaceAll('_', ' ')} · {new Date(tx.created_at).toLocaleString()}
                  </p>
                  {tx.workflow_id && (
                    <Link to={`/workflows/${tx.workflow_id}`} className="text-xs text-cyan-400 hover:text-cyan-300">
                      View workflow
                    </Link>
                  )}
                </div>
                <div className="text-right">
                  <p className={`font-mono ${Number(tx.amount_usd) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {Number(tx.amount_usd) >= 0 ? '+' : ''}${Number(tx.amount_usd).toFixed(4)}
                  </p>
                  <p className="text-xs text-[var(--color-muted)]">bal ${Number(tx.balance_after_usd).toFixed(2)}</p>
                </div>
              </li>
              )
            })}
          </ul>
        )}
      </section>
    </div>
  )
}