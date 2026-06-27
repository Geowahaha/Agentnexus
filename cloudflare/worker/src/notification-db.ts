import type { NotificationRecord, NotifyQueueMessage } from './notification-types'

export async function ensureSchema(db: D1Database): Promise<void> {
  await db.batch([
    db.prepare(`
      CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        payload TEXT NOT NULL DEFAULT '{}',
        is_read INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
      )
    `),
    db.prepare(`CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)`),
    db.prepare(
      `CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read)`,
    ),
  ])
}

function rowToRecord(row: Record<string, unknown>): NotificationRecord {
  let payload: Record<string, unknown> = {}
  try {
    payload = JSON.parse(String(row.payload ?? '{}'))
  } catch {
    payload = {}
  }
  return {
    id: String(row.id),
    user_id: String(row.user_id),
    event_type: row.event_type as NotificationRecord['event_type'],
    title: String(row.title),
    body: String(row.body),
    payload,
    is_read: Boolean(row.is_read),
    created_at: String(row.created_at),
  }
}

export async function insertNotification(
  db: D1Database,
  message: NotifyQueueMessage,
): Promise<NotificationRecord> {
  await ensureSchema(db)
  const createdAt = new Date().toISOString()
  await db
    .prepare(
      `INSERT INTO notifications (id, user_id, event_type, title, body, payload, is_read, created_at)
       VALUES (?, ?, ?, ?, ?, ?, 0, ?)`,
    )
    .bind(
      message.id,
      message.user_id,
      message.event_type,
      message.title,
      message.body,
      JSON.stringify(message.payload ?? {}),
      createdAt,
    )
    .run()

  return {
    id: message.id,
    user_id: message.user_id,
    event_type: message.event_type,
    title: message.title,
    body: message.body,
    payload: message.payload ?? {},
    is_read: false,
    created_at: createdAt,
  }
}

export async function listNotifications(
  db: D1Database,
  userId: string,
  limit = 30,
): Promise<NotificationRecord[]> {
  await ensureSchema(db)
  const result = await db
    .prepare(
      `SELECT id, user_id, event_type, title, body, payload, is_read, created_at
       FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT ?`,
    )
    .bind(userId, limit)
    .all()

  return (result.results ?? []).map((row) => rowToRecord(row as Record<string, unknown>))
}

export async function getUnreadCount(db: D1Database, userId: string): Promise<number> {
  await ensureSchema(db)
  const result = await db
    .prepare(`SELECT COUNT(*) AS count FROM notifications WHERE user_id = ? AND is_read = 0`)
    .bind(userId)
    .first<{ count: number }>()
  return Number(result?.count ?? 0)
}

export async function markNotificationsRead(
  db: D1Database,
  userId: string,
  ids: string[],
): Promise<number> {
  await ensureSchema(db)
  if (ids.length > 0) {
    const placeholders = ids.map(() => '?').join(',')
    await db
      .prepare(
        `UPDATE notifications SET is_read = 1 WHERE user_id = ? AND id IN (${placeholders})`,
      )
      .bind(userId, ...ids)
      .run()
  } else {
    await db
      .prepare(`UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0`)
      .bind(userId)
      .run()
  }
  return getUnreadCount(db, userId)
}