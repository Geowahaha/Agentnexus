import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { NotificationEvent } from '../types'

const POLL_MS = 60000
const WS_RECONNECT_MS = 5000

function wsBaseUrl(): string {
  const apiBase = import.meta.env.VITE_API_BASE ?? '/api/v1'
  if (apiBase.startsWith('http')) {
    const url = new URL(apiBase)
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
    url.pathname = '/api/v1/notifications/ws'
    url.search = ''
    return url.toString()
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/v1/notifications/ws`
}

export function useNotifications(token: string | null) {
  const [unreadCount, setUnreadCount] = useState(0)
  const [items, setItems] = useState<NotificationEvent[]>([])
  const [toast, setToast] = useState<NotificationEvent | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<number | null>(null)

  const refresh = useCallback(async () => {
    if (!token) {
      setUnreadCount(0)
      setItems([])
      return
    }
    try {
      const list = await api.getNotifications(token, 20)
      setUnreadCount(list.unread_count)
      setItems(list.items)
    } catch {
      // fallback quiet
    }
  }, [token])

  const showToast = useCallback((notification: NotificationEvent) => {
    setToast(notification)
    window.setTimeout(() => setToast(null), 5000)
  }, [])

  const connectWs = useCallback(() => {
    if (!token) return

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    const url = `${wsBaseUrl()}?token=${encodeURIComponent(token)}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(String(event.data)) as {
          type: string
          notification?: NotificationEvent
          unread_count?: number
        }
        if (data.type === 'notification' && data.notification) {
          const notification = data.notification
          setItems((prev) => {
            if (prev.some((item) => item.id === notification.id)) return prev
            return [notification, ...prev]
          })
          setUnreadCount((count) => count + (notification.is_read ? 0 : 1))
          showToast(notification)
        }
        if (data.type === 'badge' && typeof data.unread_count === 'number') {
          setUnreadCount(data.unread_count)
        }
      } catch {
        // ignore malformed frames
      }
    }

    ws.onclose = () => {
      setConnected(false)
      if (wsRef.current === ws) wsRef.current = null
      if (reconnectTimer.current) window.clearTimeout(reconnectTimer.current)
      if (token) {
        reconnectTimer.current = window.setTimeout(connectWs, WS_RECONNECT_MS)
      }
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [token, showToast])

  useEffect(() => {
    refresh()
    connectWs()
    if (!token) return undefined

    const interval = window.setInterval(refresh, POLL_MS)
    return () => {
      window.clearInterval(interval)
      if (reconnectTimer.current) window.clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [token, refresh, connectWs])

  async function markAllRead() {
    if (!token) return
    const badge = await api.markNotificationsRead(token)
    setUnreadCount(badge.unread_count)
    setItems((prev) => prev.map((item) => ({ ...item, is_read: true })))
  }

  async function markOneRead(id: string) {
    if (!token) return
    const badge = await api.markNotificationsRead(token, [id])
    setUnreadCount(badge.unread_count)
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, is_read: true } : item)))
  }

  return { unreadCount, items, toast, connected, refresh, markAllRead, markOneRead }
}