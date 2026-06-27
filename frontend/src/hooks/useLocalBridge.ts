import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { BridgeDevice } from '../types'

export function useLocalBridge(token: string | null | undefined) {
  const [devices, setDevices] = useState<BridgeDevice[]>([])
  const [enabled, setEnabled] = useState(false)
  const [deviceId, setDeviceId] = useState('')

  useEffect(() => {
    if (!token) {
      setDevices([])
      setDeviceId('')
      return
    }
    api
      .listBridgeDevices(token)
      .then((list) => {
        setDevices(list)
        setDeviceId((current) => {
          if (current && list.some((device) => device.id === current)) return current
          return list[0]?.id ?? ''
        })
      })
      .catch(() => setDevices([]))
  }, [token])

  const bridgeDeviceId = enabled && deviceId ? deviceId : undefined

  return {
    devices,
    enabled,
    setEnabled,
    deviceId,
    setDeviceId,
    bridgeDeviceId,
  }
}