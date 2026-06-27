import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

type Props = { children: ReactNode }
type State = { error: Error | null }

export class RouteErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Route render failed', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <p className="text-xs font-semibold uppercase tracking-widest text-amber-600">Page error</p>
        <h1 className="mt-2 text-2xl font-bold text-[var(--color-text)]">Something went wrong loading this page</h1>
        <p className="mt-3 text-sm text-[var(--color-muted)]">
          Try refreshing. If you use an ad blocker or browser extension, disable it for obolla.com and retry.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <button
            type="button"
            onClick={() => this.setState({ error: null })}
            className="rounded-lg bg-[var(--color-market)] px-5 py-2.5 text-sm font-bold text-white"
          >
            Try again
          </button>
          <Link
            to="/"
            className="rounded-lg border border-[var(--color-border)] px-5 py-2.5 text-sm font-semibold text-[var(--color-text)]"
          >
            Back to marketplace
          </Link>
        </div>
      </div>
    )
  }
}