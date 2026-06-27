export type NotificationEventType = 'new_review' | 'thread_reply' | 'thread_resolved'

export interface NotificationRecord {
  id: string
  user_id: string
  event_type: NotificationEventType
  title: string
  body: string
  payload: Record<string, unknown>
  is_read: boolean
  created_at: string
}

export interface NotifyQueueMessage {
  id: string
  user_id: string
  event_type: NotificationEventType
  title: string
  body: string
  payload: Record<string, unknown>
}

export interface WsServerMessage {
  type: 'notification' | 'badge' | 'connected'
  notification?: NotificationRecord
  unread_count?: number
}