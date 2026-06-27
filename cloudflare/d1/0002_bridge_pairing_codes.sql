CREATE TABLE IF NOT EXISTS bridge_pairing_codes (
  code TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  used_at INTEGER,
  created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bridge_pairing_user ON bridge_pairing_codes(user_id);