import { Link } from 'react-router-dom'
import type { BridgeDevice } from '../types'
import { useLocale } from '../context/LocaleContext'

type LocalBridgeSelectorProps = {
  devices: BridgeDevice[]
  enabled: boolean
  onEnabledChange: (enabled: boolean) => void
  deviceId: string
  onDeviceIdChange: (deviceId: string) => void
  hint?: string
}

export function LocalBridgeSelector({
  devices,
  enabled,
  onEnabledChange,
  deviceId,
  onDeviceIdChange,
  hint,
}: LocalBridgeSelectorProps) {
  const { tr } = useLocale()

  return (
    <div className="rounded-lg border border-violet-200 bg-violet-50/90 p-4 space-y-3">
      {devices.length === 0 ? (
        <p className="text-xs font-medium text-[var(--color-text-soft)]">
          <Link to="/bridge" className="font-semibold text-[var(--color-market-hover)] hover:underline">
            {tr('bridgeConnect')}
          </Link>{' '}
          {tr('bridgeIntro')}
        </p>
      ) : (
        <>
          <label className="flex items-center gap-2 text-sm font-medium text-[var(--color-text)] cursor-pointer">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => onEnabledChange(e.target.checked)}
              className="rounded border-[var(--color-border)] bg-[var(--color-surface)] text-violet-500"
            />
            {tr('bridgeUseMachine')}
          </label>
          {enabled && (
            <div>
              <label className="block text-xs font-semibold text-[var(--color-text-soft)] mb-1">{tr('bridgeDevice')}</label>
              <select
                value={deviceId}
                onChange={(e) => onDeviceIdChange(e.target.value)}
                className="w-full rounded-lg border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text)]"
              >
                {devices.map((device) => (
                  <option key={device.id} value={device.id}>
                    {device.device_name}
                    {device.capabilities?.includes('write') ? ' (read/write/exec)' : ' (read-only)'}
                  </option>
                ))}
              </select>
              <p className="mt-2 text-xs font-medium text-readable-muted">
                {hint ?? (
                  <>
                    Keep <code className="font-mono font-semibold text-violet-950">agentnexus-bridge connect</code> running.
                    Agents get <code className="font-mono font-semibold text-violet-950">bridge.*</code> tools automatically.
                    Write and shell commands require <code className="font-mono font-semibold text-violet-950">[y/N]</code>{' '}
                    approval in the Bridge terminal.
                  </>
                )}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}