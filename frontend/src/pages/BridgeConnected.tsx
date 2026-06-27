export function BridgeConnected() {
  return (
    <div className="mx-auto max-w-lg px-4 py-16 text-center sm:px-6">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/20 text-3xl text-emerald-400">
        ✓
      </div>
      <h1 className="mt-6 text-2xl font-bold text-[var(--color-text)]">This PC is connected</h1>
      <p className="mt-3 text-sm text-[var(--color-muted)]">
        Your support agent can now see this machine on their dashboard. You can close this browser
        window — the bridge keeps running in the background.
      </p>
      <p className="mt-6 text-xs text-amber-300/90">
        If an agent asks to write a file or run a command, you will get a popup or terminal prompt
        to approve.
      </p>
    </div>
  )
}