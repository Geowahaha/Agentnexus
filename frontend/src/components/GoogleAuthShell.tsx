import { GoogleOAuthProvider } from '@react-oauth/google'
import type { ReactNode } from 'react'

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? ''

/** Load Google Identity script only on auth pages — avoids global DOM crashes when blocked. */
export function GoogleAuthShell({ children }: { children: ReactNode }) {
  if (!googleClientId) return <>{children}</>
  return <GoogleOAuthProvider clientId={googleClientId}>{children}</GoogleOAuthProvider>
}