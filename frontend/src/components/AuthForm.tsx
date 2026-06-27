import { GoogleLogin, type CredentialResponse } from '@react-oauth/google'
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

interface AuthFormProps {
  mode: 'login' | 'register'
  returnTo?: string
  signupCredits?: number
  googleEnabled?: boolean
  onSubmit: (email: string, password: string, fullName?: string) => Promise<void>
  onGoogleSignIn?: (idToken: string) => Promise<void>
}

function EyeIcon({ open }: { open: boolean }) {
  if (open) {
    return (
      <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
        />
      </svg>
    )
  }
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"
      />
    </svg>
  )
}

function GoogleIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  )
}

export function AuthForm({
  mode,
  returnTo,
  signupCredits = 5,
  googleEnabled = false,
  onSubmit,
  onGoogleSignIn,
}: AuthFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)

  async function handleGoogleSuccess(response: CredentialResponse) {
    if (!onGoogleSignIn || !response.credential) return
    setError('')
    setGoogleLoading(true)
    try {
      await onGoogleSignIn(response.credential)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Google sign-in failed')
    } finally {
      setGoogleLoading(false)
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onSubmit(email, password, fullName || undefined)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const busy = loading || googleLoading

  return (
    <div className="mx-auto w-full max-w-md">
      <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-8 shadow-xl">
        <h1 className="text-2xl font-semibold text-[var(--color-text)]">
          {mode === 'login' ? 'Welcome back' : 'Create account'}
        </h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          {mode === 'login'
            ? 'Sign in to run Expert Skills and manage workflows'
            : `Get $${signupCredits.toFixed(0)} trial credits — try any agent or skill. Agent owners are not paid from trial usage (see Terms).`}
        </p>
        {returnTo && returnTo !== '/dashboard' && (
          <p className="mt-2 text-xs text-amber-400/90">
            You will return to checkout after {mode === 'login' ? 'sign in' : 'registration'}.
          </p>
        )}

        {googleEnabled && onGoogleSignIn && (
          <>
            <div className="mt-6 flex justify-center">
              {googleLoading ? (
                <button
                  type="button"
                  disabled
                  className="flex w-full items-center justify-center gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] py-2.5 text-sm font-medium text-[var(--color-text)] opacity-50"
                >
                  <GoogleIcon />
                  Signing in with Google…
                </button>
              ) : (
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={() => setError('Google sign-in was cancelled or failed')}
                  theme="filled_black"
                  size="large"
                  text={mode === 'login' ? 'signin_with' : 'signup_with'}
                  shape="rectangular"
                  width={352}
                />
              )}
            </div>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[var(--color-border)]" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-[var(--color-surface-raised)] px-2 text-[var(--color-muted)]">
                  or continue with email
                </span>
              </div>
            </div>
          </>
        )}

        <form onSubmit={handleSubmit} className={googleEnabled ? 'space-y-4' : 'mt-6 space-y-4'}>
          {mode === 'register' && (
            <div>
              <label className="block text-xs font-medium text-[var(--color-muted)] mb-1.5">Full name</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-sm text-white placeholder:text-[var(--color-muted)] focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
                placeholder="Jane Doe"
              />
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-[var(--color-muted)] mb-1.5">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-sm text-white placeholder:text-[var(--color-muted)] focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--color-muted)] mb-1.5">Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                required
                minLength={mode === 'register' ? 8 : 1}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 pr-11 text-sm text-white placeholder:text-[var(--color-muted)] focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword((visible) => !visible)}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-[var(--color-muted)] hover:text-[var(--color-text-soft)] focus:outline-none focus-visible:text-cyan-400"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                aria-pressed={showPassword}
              >
                <EyeIcon open={showPassword} />
              </button>
            </div>
          </div>

          {error && (
            <p className="rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-sm text-red-400">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-cyan-500 py-2.5 text-sm font-semibold text-slate-900 hover:bg-cyan-400 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--color-muted)]">
          {mode === 'login' ? (
            <>
              No account?{' '}
              <Link
                to="/register"
                state={returnTo ? { from: { pathname: returnTo } } : undefined}
                className="text-cyan-400 hover:text-cyan-300"
              >
                Sign up
              </Link>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <Link
                to="/login"
                state={returnTo ? { from: { pathname: returnTo } } : undefined}
                className="text-cyan-400 hover:text-cyan-300"
              >
                Sign in
              </Link>
            </>
          )}
        </p>
      </div>
    </div>
  )
}