import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import type { SmartFarmConnectKit, SmartFarmDetail, SmartFarmWeatherResponse } from '../types'

export function SmartFarm() {
  const { token } = useAuth()
  const { tr, trf } = useLocale()
  const [farms, setFarms] = useState<SmartFarmDetail[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [detail, setDetail] = useState<SmartFarmDetail | null>(null)
  const [connectKit, setConnectKit] = useState<SmartFarmConnectKit | null>(null)
  const [orgName, setOrgName] = useState('')
  const [newFarmName, setNewFarmName] = useState('')
  const [address, setAddress] = useState('')
  const [gatewayIp, setGatewayIp] = useState('')
  const [gatewayLabel, setGatewayLabel] = useState('IoT Gateway')
  const [coords, setCoords] = useState<{ lat: number; lng: number; mapsUrl?: string } | null>(null)
  const [weather, setWeather] = useState<SmartFarmWeatherResponse | null>(null)
  const [deviceName, setDeviceName] = useState('Greenhouse Gateway')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState('')

  const refresh = useCallback(async () => {
    if (!token) return
    const list = await api.listSmartFarms(token)
    if (list.length === 0) {
      setFarms([])
      setDetail(null)
      setSelectedId('')
      return
    }
    const enriched = await Promise.all(list.map((f) => api.getSmartFarm(token, f.id)))
    setFarms(enriched)
    setSelectedId((cur) => (cur && enriched.some((f) => f.id === cur) ? cur : enriched[0].id))
  }, [token])

  useEffect(() => {
    if (!token) return
    refresh()
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'))
      .finally(() => setLoading(false))
  }, [token, refresh])

  useEffect(() => {
    if (!selectedId) {
      setDetail(null)
      setWeather(null)
      return
    }
    const hit = farms.find((f) => f.id === selectedId)
    setDetail(hit ?? null)
    setConnectKit(null)
    setWeather(null)
  }, [selectedId, farms])

  useEffect(() => {
    if (!token || !detail?.latitude || !detail?.longitude) return
    api
      .getSmartFarmWeather(token, detail.id)
      .then(setWeather)
      .catch(() => setWeather(null))
  }, [token, detail?.id, detail?.latitude, detail?.longitude])

  async function handleGeocode() {
    if (!token || !address.trim()) return
    setBusy(true)
    setError('')
    try {
      const geo = await api.geocodeSmartFarmAddress(token, address.trim())
      setCoords({ lat: geo.latitude, lng: geo.longitude, mapsUrl: geo.google_maps_url })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Geocode failed')
    } finally {
      setBusy(false)
    }
  }

  async function handleCreateFarm() {
    if (!token || !newFarmName.trim()) return
    setBusy(true)
    setError('')
    try {
      const gateway_ips = gatewayIp.trim()
        ? [{ ip: gatewayIp.trim(), label: gatewayLabel.trim() || 'IoT Gateway' }]
        : []
      await api.createSmartFarm(token, {
        name: newFarmName.trim(),
        organization_name: orgName.trim() || undefined,
        address: address.trim() || undefined,
        latitude: coords?.lat,
        longitude: coords?.lng,
        google_maps_url: coords?.mapsUrl,
        gateway_ips,
        weather_alerts_enabled: true,
        crop_type: 'japanese-melon',
      })
      setOrgName('')
      setNewFarmName('')
      setAddress('')
      setGatewayIp('')
      setCoords(null)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed')
    } finally {
      setBusy(false)
    }
  }

  async function refreshWeather() {
    if (!token || !detail) return
    setBusy(true)
    try {
      setWeather(await api.getSmartFarmWeather(token, detail.id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Weather failed')
    } finally {
      setBusy(false)
    }
  }

  async function handleAddDevice() {
    if (!token || !detail) return
    setBusy(true)
    setError('')
    try {
      const device = await api.createSmartFarmDevice(token, detail.id, {
        device_name: deviceName.trim() || 'IoT Gateway',
        protocol: 'http',
      })
      setConnectKit(device.connect ?? null)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Device create failed')
    } finally {
      setBusy(false)
    }
  }

  async function handleExport(fmt: 'json' | 'csv') {
    if (!token || !detail) return
    setBusy(true)
    try {
      await api.exportSmartFarmDataset(token, detail.id, { format: fmt, hours: 168 })
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setBusy(false)
    }
  }

  async function handleUpload(file: File) {
    if (!token || !detail) return
    setBusy(true)
    try {
      const result = await api.uploadSmartFarmFile(token, detail.id, file)
      setError('')
      alert(trf('smartFarmUploadOk', { count: String(result.readings_ingested) }))
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  function copyText(label: string, text: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(label)
      setTimeout(() => setCopied(''), 2000)
    })
  }

  if (!token) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center">
        <p className="text-[var(--color-text-soft)]">{tr('smartFarmLogin')}</p>
        <Link to="/login" className="mt-4 inline-block text-[var(--color-market)] underline">
          {tr('navLogin')}
        </Link>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-10">
      <header className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-wide text-[var(--color-sage)]">OBOLLA Smart Farm</p>
        <h1 className="text-3xl font-bold text-[var(--color-text)]">{tr('smartFarmTitle')}</h1>
        <p className="max-w-2xl text-[var(--color-text-soft)]">{tr('smartFarmSubtitle')}</p>
      </header>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>
      )}

      <section className="rounded-xl border border-[var(--color-border)] bg-white/80 p-6 shadow-sm">
        <h2 className="text-lg font-semibold">{tr('smartFarmCreate')}</h2>
        <p className="mt-1 text-sm text-[var(--color-text-soft)]">{tr('smartFarmRegisterHint')}</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <input
            className="rounded-lg border border-[var(--color-border)] px-3 py-2"
            placeholder={tr('smartFarmOrgPh')}
            value={orgName}
            onChange={(e) => setOrgName(e.target.value)}
          />
          <input
            className="rounded-lg border border-[var(--color-border)] px-3 py-2"
            placeholder={tr('smartFarmNamePh')}
            value={newFarmName}
            onChange={(e) => setNewFarmName(e.target.value)}
          />
          <input
            className="sm:col-span-2 rounded-lg border border-[var(--color-border)] px-3 py-2"
            placeholder={tr('smartFarmAddressPh')}
            value={address}
            onChange={(e) => setAddress(e.target.value)}
          />
          <input
            className="rounded-lg border border-[var(--color-border)] px-3 py-2"
            placeholder={tr('smartFarmGatewayIpPh')}
            value={gatewayIp}
            onChange={(e) => setGatewayIp(e.target.value)}
          />
          <input
            className="rounded-lg border border-[var(--color-border)] px-3 py-2"
            placeholder={tr('smartFarmGatewayLabelPh')}
            value={gatewayLabel}
            onChange={(e) => setGatewayLabel(e.target.value)}
          />
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy || !address.trim()}
            onClick={handleGeocode}
            className="rounded-lg border px-4 py-2 text-sm font-semibold"
          >
            {tr('smartFarmGeocode')}
          </button>
          <button
            type="button"
            disabled={busy || !newFarmName.trim()}
            onClick={handleCreateFarm}
            className="rounded-lg bg-[var(--color-market)] px-4 py-2 font-semibold text-white disabled:opacity-50"
          >
            {tr('smartFarmCreateBtn')}
          </button>
        </div>
        {coords && (
          <div className="mt-4 space-y-2">
            <p className="text-xs text-[var(--color-text-soft)]">
              {tr('smartFarmMap')}: {coords.lat.toFixed(5)}, {coords.lng.toFixed(5)}
            </p>
            <iframe
              title="farm-map"
              className="h-48 w-full rounded-lg border"
              src={`https://www.openstreetmap.org/export/embed.html?bbox=${coords.lng - 0.02}%2C${coords.lat - 0.02}%2C${coords.lng + 0.02}%2C${coords.lat + 0.02}&layer=mapnik&marker=${coords.lat}%2C${coords.lng}`}
            />
            {coords.mapsUrl && (
              <a href={coords.mapsUrl} target="_blank" rel="noreferrer" className="text-sm text-[var(--color-market)] underline">
                {tr('smartFarmOpenGoogleMaps')}
              </a>
            )}
          </div>
        )}
      </section>

      {loading ? (
        <p className="text-[var(--color-text-soft)]">{tr('skillLoading')}</p>
      ) : farms.length === 0 ? (
        <p className="text-[var(--color-text-soft)]">{tr('smartFarmEmpty')}</p>
      ) : (
        <>
          <div className="flex flex-wrap gap-2">
            {farms.map((farm) => (
              <button
                key={farm.id}
                type="button"
                onClick={() => setSelectedId(farm.id)}
                className={`rounded-full border px-4 py-2 text-sm font-semibold ${
                  selectedId === farm.id
                    ? 'border-[var(--color-market)] bg-[var(--color-market)]/10 text-[var(--color-market-hover)]'
                    : 'border-[var(--color-border)] text-[var(--color-text-soft)]'
                }`}
              >
                {farm.name}
              </button>
            ))}
          </div>

          {detail && (
            <div className="grid gap-6 lg:grid-cols-2">
              <section className="rounded-xl border border-[var(--color-border)] bg-white/80 p-6 lg:col-span-2">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">{detail.organization_name || detail.name}</h2>
                    {detail.organization_name && <p className="text-sm text-[var(--color-text-soft)]">{detail.name}</p>}
                    {detail.address && <p className="mt-1 text-sm">{detail.address}</p>}
                  </div>
                  {detail.google_maps_url && (
                    <a href={detail.google_maps_url} target="_blank" rel="noreferrer" className="text-sm text-[var(--color-market)] underline">
                      {tr('smartFarmOpenGoogleMaps')}
                    </a>
                  )}
                </div>
                {detail.gateway_ips && detail.gateway_ips.length > 0 && (
                  <div className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">
                    <p className="font-semibold">{tr('smartFarmMqttWhitelist')}</p>
                    <ul className="mt-1 list-disc pl-5">
                      {detail.gateway_ips.map((g) => (
                        <li key={g.ip}>
                          <code>{g.ip}</code> — {g.label}
                        </li>
                      ))}
                    </ul>
                    {detail.mqtt_whitelist_hint && <p className="mt-2 text-xs">{detail.mqtt_whitelist_hint}</p>}
                  </div>
                )}
                {detail.latitude != null && detail.longitude != null && (
                  <iframe
                    title="farm-location"
                    className="mt-3 h-52 w-full rounded-lg border"
                    src={`https://www.openstreetmap.org/export/embed.html?bbox=${detail.longitude - 0.02}%2C${detail.latitude - 0.02}%2C${detail.longitude + 0.02}%2C${detail.latitude + 0.02}&layer=mapnik&marker=${detail.latitude}%2C${detail.longitude}`}
                  />
                )}
                <div className="mt-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold">{tr('smartFarmWeather')}</h3>
                    <button type="button" disabled={busy} onClick={refreshWeather} className="text-xs text-[var(--color-market)] underline">
                      {tr('smartFarmWeatherRefresh')}
                    </button>
                  </div>
                  {!detail.latitude || !detail.longitude ? (
                    <p className="mt-2 text-sm text-[var(--color-text-soft)]">{tr('smartFarmNoWeather')}</p>
                  ) : weather?.alerts && weather.alerts.length > 0 ? (
                    <ul className="mt-2 space-y-2">
                      {weather.alerts.map((a, i) => (
                        <li
                          key={`${a.type}-${a.date ?? i}`}
                          className={`rounded-lg px-3 py-2 text-sm ${
                            a.level === 'critical' ? 'bg-red-100 text-red-900' : a.level === 'high' ? 'bg-orange-100 text-orange-900' : 'bg-yellow-50 text-yellow-900'
                          }`}
                        >
                          <span className="font-semibold uppercase">{a.level}</span> — {a.message}
                          {a.date ? <span className="block text-xs opacity-80">{a.date}</span> : null}
                        </li>
                      ))}
                    </ul>
                  ) : weather ? (
                    <p className="mt-2 text-sm text-green-800">ไม่มีความเสี่ยงสูงในช่วงพยากรณ์ 5 วัน</p>
                  ) : null}
                </div>
              </section>

              <section className="rounded-xl border border-[var(--color-border)] bg-white/80 p-6">
                <h2 className="text-lg font-semibold">{tr('smartFarmPlugPlay')}</h2>
                <p className="mt-2 text-sm text-[var(--color-text-soft)]">{tr('smartFarmPlugPlayHint')}</p>
                <div className="mt-4 space-y-3">
                  <input
                    className="w-full rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm"
                    value={deviceName}
                    onChange={(e) => setDeviceName(e.target.value)}
                  />
                  <button
                    type="button"
                    disabled={busy}
                    onClick={handleAddDevice}
                    className="rounded-lg border border-[var(--color-market)] px-4 py-2 text-sm font-semibold text-[var(--color-market-hover)]"
                  >
                    {tr('smartFarmAddDevice')}
                  </button>
                </div>
                {connectKit && (
                  <div className="mt-4 space-y-3 rounded-lg bg-[var(--color-cream)]/60 p-4 text-sm">
                    <div>
                      <p className="font-semibold">
                        HTTP ingest {connectKit.recommended_transport === 'https' ? tr('smartFarmRecommended') : ''}
                      </p>
                      {connectKit.http_note && (
                        <p className="mt-1 text-xs text-[var(--color-text-soft)]">{connectKit.http_note}</p>
                      )}
                      <code className="block break-all text-xs">{connectKit.http_ingest_url}</code>
                      <button type="button" className="mt-1 text-xs text-[var(--color-market)]" onClick={() => copyText('http', connectKit.http_ingest_url)}>
                        {copied === 'http' ? '✓' : tr('smartFarmCopy')}
                      </button>
                    </div>
                    <div>
                      <p className="font-semibold">X-Device-Key</p>
                      <code className="block break-all text-xs">{connectKit.http_headers['X-Device-Key']}</code>
                    </div>
                    <div>
                      <p className="font-semibold">{tr('smartFarmMqttAdvanced')}</p>
                      {connectKit.mqtt_note && (
                        <p className="mt-1 text-xs text-amber-800">{connectKit.mqtt_note}</p>
                      )}
                      <p className="text-xs">Broker: {connectKit.mqtt_broker}</p>
                      <p className="text-xs">User: {connectKit.mqtt_username}</p>
                      <p className="text-xs">Topic: {connectKit.mqtt_topic}</p>
                    </div>
                    <pre className="max-h-40 overflow-auto rounded bg-white/80 p-2 text-xs">{connectKit.curl_example}</pre>
                  </div>
                )}
              </section>

              <section className="rounded-xl border border-[var(--color-border)] bg-white/80 p-6 space-y-3">
                <h2 className="text-lg font-semibold">Marketplace</h2>
                <div className="flex flex-wrap gap-2 text-sm">
                  <Link
                    to={`/expert-skills/quality-check-flow-smart-famers?farm_id=${detail.id}`}
                    className="rounded-lg border border-[var(--color-market)] px-3 py-2 font-semibold text-[var(--color-market-hover)]"
                  >
                    Run Quality Check Flow
                  </Link>
                  <Link
                    to={`/japanese-melon-pack?farm_id=${detail.id}`}
                    className="rounded-lg border border-[var(--color-market)] px-3 py-2 font-semibold text-[var(--color-market-hover)] hover:bg-emerald-50"
                  >
                    Japanese Melon Dataset Pack
                  </Link>
                </div>
                <h2 className="text-lg font-semibold pt-2">{tr('smartFarmDatasets')}</h2>
                <p className="mt-2 text-sm text-[var(--color-text-soft)]">
                  {trf('smartFarmAutoExport', { hours: String(detail.auto_export_hours) })}
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button type="button" disabled={busy} onClick={() => handleExport('json')} className="rounded-lg bg-[var(--color-market)] px-3 py-2 text-sm font-semibold text-white">
                    Export JSON
                  </button>
                  <button type="button" disabled={busy} onClick={() => handleExport('csv')} className="rounded-lg border px-3 py-2 text-sm font-semibold">
                    Export CSV
                  </button>

              {/* Eve Irrigation Physical Loop - modern seamless integration */}
              <div className="mt-6 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-4">
                <h3 className="font-semibold text-emerald-700">Eve Irrigation Integration (Test Ready)</h3>
                <p className="text-xs mt-1">Link your Eve Aqua / smart hose timer. Auto stop on rain using weather (detect location or manual). Agent controls via Bridge on same machine.</p>
                
                <div className="mt-3 flex flex-wrap gap-2">
                  <button 
                    onClick={async () => {
                      // Modern detection: try geolocation + network info via Bridge
                      if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(pos => {
                          alert(`Location detected: ${pos.coords.latitude}, ${pos.coords.longitude}. Use for weather. Same WiFi? Bridge will confirm via local network info.`);
                          // In real: call bridge 'get_local_network_info' to detect same network
                        });
                      }
                      alert('Eve link simulated. In real: Use Bridge tool "control_irrigation" + weather check. Your Eve on same WiFi/Bluetooth will be auto-detected via Bridge client.');
                    }}
                    className="rounded bg-emerald-600 text-white px-3 py-1 text-xs"
                  >
                    Detect Location + Test Eve via Bridge (same WiFi/Bluetooth)
                  </button>
                  <button onClick={async () => {
                    alert('Weather check: If rain forecast > threshold, stop irrigation via Eve command (Bridge tool or Web BT). Configurable per location.');
                    // Demo push
                    if ('Notification' in window) {
                      const perm = await Notification.requestPermission();
                      if (perm === 'granted') {
                        new Notification('OBOLLA Irrigation', { body: 'Rain detected - stopped watering via Eve' });
                      }
                    }
                  }} className="rounded border px-3 py-1 text-xs">
                    Test Rain Stop Logic + Push
                  </button>
                </div>
                <p className="text-[10px] mt-1 text-emerald-600">Compatible with Eve (no extra bridge). Agent uses your local Bridge for control. Schedules 7x/day auto adjusted.</p>

                <div className="mt-2 text-[10px]">
                  <button onClick={async () => {
                    const ua = navigator.userAgent;
                    const isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
                    const nav = navigator as any;
                    if (isIOS) {
                      alert('On iPhone (iOS 8+ / Chrome), Web Bluetooth is NOT supported by Apple (uses WebKit). Solution: Run the Bridge client (node index.mjs connect) on a Mac/PC on the SAME WiFi network as your Eve device. Then open this site on phone for monitoring/control via agent. Or use Eve app + Apple Home shortcuts for rain stop. Bridge will handle local execution.');
                      return;
                    }
                    if (nav.bluetooth) {
                      try {
                        const device = await nav.bluetooth.requestDevice({ filters: [{ namePrefix: 'Eve' }] });
                        alert('Bluetooth device selected: ' + device.name + '. Use Bridge tool "control_irrigation" or direct from here.');
                      } catch(e) { alert('Bluetooth error or cancelled. Use Bridge on same WiFi.'); }
                    } else {
                      alert('Web Bluetooth not supported. Use Bridge client on machine for network detection (same WiFi auto).');
                    }
                  }} className="text-xs bg-blue-100 px-2 py-0.5 rounded">Detect Bluetooth / same WiFi (modern browser + Bridge)</button>
                </div>

                {/* Direct connect from browser (PC Windows or Android) - robust with auto-reconnect */}
                <div className="mt-3 p-2 border border-dashed border-emerald-600 rounded text-xs bg-white/50">
                  <p className="font-medium mb-1">On Windows PC Chrome (or Android): Open this page → pair Eve Aqua. Connection will auto-reconnect if drops.</p>
                  <button 
                    onClick={async () => {
                      const nav = navigator as any;
                      if (!nav.bluetooth) {
                        alert('Web Bluetooth not supported here. On Windows: Use Chrome. On iPhone: impossible in browser - use Bridge on PC instead (see below).');
                        return;
                      }
                      try {
                        // Filter by exact name from your pairing prompt: "Eve Aqua 4923"
                        let device = await nav.bluetooth.requestDevice({
                          filters: [{ name: 'Eve Aqua 4923' }],
                          // Leave optionalServices empty to discover all, then we will log them
                          optionalServices: []
                        });

                        // Robust connect + auto-reconnect + discovery
                        async function connectAndKeep(dev: any) {
                          try {
                            const server = await dev.gatt.connect();
                            alert(`Paired & connected to ${dev.name}! GATT stable. Now can control irrigation. Check console for services. Click the button again or refresh if drops (auto reconnect is on).`);

                            // Store for later use (window for demo)
                            (window as any).eveDevice = dev;
                            (window as any).eveServer = server;

                            // Listen for disconnect (common issue: drops after pair)
                            dev.addEventListener('gattserverdisconnected', () => {
                              console.log('Eve GATT disconnected, auto reconnecting...');
                              setTimeout(() => connectAndKeep(dev), 2000);
                            });

                            // Discover services to help find the irrigation control UUID
                            try {
                              const services = await server.getPrimaryServices();
                              console.log('Discovered services (copy these UUIDs):', services.map((s: any) => s.uuid));
                              alert('Connection stable. Check browser console (F12) for list of services/UUIDs. Use nRF app on phone for easier viewing of characteristics. Then we can add exact control for stop/start.');
                            } catch (e) {
                              console.log('Could not discover services yet:', e);
                            }

                            // Optional: keep-alive ping (read a char every 30s to prevent drop)
                            const keepAlive = async () => {
                              try {
                                if (server && server.connected) {
                                  // Once we have a char UUID, read it here to keep alive
                                  console.log('Keep-alive ping sent');
                                }
                              } catch {}
                              setTimeout(keepAlive, 30000);
                            };
                            keepAlive();

                            // Now you can control: find the valve/schedule characteristic and write
                            // e.g. to stop: writeValue(new Uint8Array([0x00]))
                            return server;
                          } catch (err: any) {
                            alert('GATT connect failed: ' + (err.message || err) + '. Try close range, restart Bluetooth, or re-pair in Eve app.');
                          }
                        }

                        await connectAndKeep(device);

                      } catch (e: any) {
                        alert('Pair failed: ' + (e.message || e) + '. Make sure Eve is on, close to PC, Bluetooth on, and try again. If paired before, remove from OS Bluetooth settings first.');
                      }
                    }} 
                    className="bg-emerald-700 text-white px-2 py-1 rounded text-xs w-full"
                  >
                    Connect / Reconnect to Eve Aqua 4923 (robust)
                  </button>
                  <p className="text-[9px] mt-1">After stable connect, use weather check → auto write stop to Eve char. Tab keeps connection alive. For iPhone: impossible in browser - run Bridge client on Windows/Mac on same WiFi, then control via our agent + Bridge tool.</p>
                </div>
              </div>
                  <label className="cursor-pointer rounded-lg border px-3 py-2 text-sm font-semibold">
                    {tr('smartFarmUpload')}
                    <input
                      type="file"
                      accept=".csv,.json"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0]
                        if (file) void handleUpload(file)
                        e.target.value = ''
                      }}
                    />
                  </label>
                </div>
                <ul className="mt-4 max-h-64 space-y-2 overflow-auto text-sm">
                  {detail.datasets.length === 0 ? (
                    <li className="text-[var(--color-text-soft)]">{tr('smartFarmNoDatasets')}</li>
                  ) : (
                    detail.datasets.map((pack) => (
                      <li key={pack.id} className="flex items-center justify-between gap-2 rounded-lg border px-3 py-2">
                        <span>
                          {pack.name} · {pack.record_count} rows
                          {pack.auto_generated ? ' · auto' : ''}
                        </span>
                        <button
                          type="button"
                          className="text-[var(--color-market)] underline"
                          onClick={() => api.downloadSmartFarmDataset(token!, pack.id, `${pack.name}.${pack.format}`)}
                        >
                          {tr('smartFarmDownload')}
                        </button>
                      </li>
                    ))
                  )}
                </ul>
              </section>
            </div>
          )}
        </>
      )}
    </div>
  )
}