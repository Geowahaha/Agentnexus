import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { AuthForm } from '../components/AuthForm'
import { GoogleAuthShell } from '../components/GoogleAuthShell'
import { useAuth } from '../context/AuthContext'

function returnPath(state: unknown): string {
  if (
    state &&
    typeof state === 'object' &&
    'from' in state &&
    state.from &&
    typeof state.from === 'object' &&
    'pathname' in state.from &&
    typeof state.from.pathname === 'string'
  ) {
    const from = state.from as { pathname: string; search?: string }
    return `${from.pathname}${from.search ?? ''}`
  }
  return '/dashboard'
}

const googleEnabled = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID)

export function Login() {
  const { login, loginWithGoogle, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const redirectTo = returnPath(location.state)

  if (user) return <Navigate to={redirectTo} replace />

  return (
    <GoogleAuthShell>
    <div className="px-4 py-16">
      <AuthForm
        mode="login"
        returnTo={redirectTo}
        googleEnabled={googleEnabled}
        onSubmit={async (email, password) => {
          await login(email, password)
          navigate(redirectTo)
        }}
        onGoogleSignIn={async (idToken) => {
          await loginWithGoogle(idToken)
          navigate(redirectTo)
        }}
      />
    </div>
    </GoogleAuthShell>
  )
}