import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { RouteErrorBoundary } from './components/RouteErrorBoundary'
import { CustomerJoinLayout } from './components/CustomerJoinLayout'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import { AgentDetail } from './pages/AgentDetail'
import { ExpertSkillDetail } from './pages/ExpertSkillDetail'
import { Billing } from './pages/Billing'
import { BridgeDevices } from './pages/BridgeDevices'
import { BridgeConnected } from './pages/BridgeConnected'
import { BridgeJoin } from './pages/BridgeJoin'
import { CreatorDashboard } from './pages/CreatorDashboard'
import { CreatorProductEditor } from './pages/creator/CreatorProductEditor'
import { CreatorProfile } from './pages/CreatorProfile'
import { Security } from './pages/Security'
import { Dashboard } from './pages/Dashboard'
import { Login } from './pages/Login'
import { Legal } from './pages/Legal'
import { Community } from './pages/Community'
import { CreatorGarden } from './pages/CreatorGarden'
import { Marketplace } from './pages/Marketplace'
import { Pricing } from './pages/Pricing'
import { ShowcaseDetail } from './pages/ShowcaseDetail'
import { Register } from './pages/Register'
import { SmartFarm } from './pages/SmartFarm'
import { Workflow } from './pages/Workflow'
import { AgentReadyPro } from './pages/AgentReadyPro'
import { JapaneseMelonPack } from './pages/JapaneseMelonPack'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <RouteErrorBoundary>
        <Routes>
          <Route element={<CustomerJoinLayout />}>
            <Route path="bridge/join" element={<BridgeJoin />} />
            <Route path="bridge/connected" element={<BridgeConnected />} />
          </Route>
          <Route element={<Layout />}>
            <Route index element={<Marketplace />} />
            <Route path="login" element={<Login />} />
            <Route path="register" element={<Register />} />
            <Route path="agents/:id" element={<AgentDetail />} />
            {/* Flagship Agent-Ready Auto Fix Pro - canonical clean URL */}
            <Route path="agent-ready" element={<AgentReadyPro />} />
            {/* Redirect old /expert-skills/ID to the preferred /agent-ready for consistency */}
            <Route path="expert-skills/33333333-3333-4333-8333-333333333310" element={<Navigate to="/agent-ready" replace />} />
            <Route path="expert-skills/:id" element={<ExpertSkillDetail />} />
            <Route path="expert-skills/japanese-melon-dataset-pack" element={<JapaneseMelonPack />} />
            <Route path="japanese-melon-pack" element={<JapaneseMelonPack />} />
            <Route path="creators/:ownerId" element={<CreatorProfile />} />
            <Route path="security" element={<Security />} />
            <Route path="showcases/:showcaseId" element={<ShowcaseDetail />} />
            <Route path="community" element={<Community />} />
            <Route
              path="smart-farm"
              element={
                <ProtectedRoute>
                  <SmartFarm />
                </ProtectedRoute>
              }
            />
            <Route path="garden" element={<CreatorGarden />} />
            <Route path="pricing" element={<Pricing />} />
            <Route path="terms" element={<Legal kind="terms" />} />
            <Route path="privacy" element={<Legal kind="privacy" />} />
            <Route path="refunds" element={<Legal kind="refunds" />} />
            <Route
              path="dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="creator"
              element={
                <ProtectedRoute>
                  <CreatorDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="creator/products/new"
              element={
                <ProtectedRoute>
                  <CreatorProductEditor />
                </ProtectedRoute>
              }
            />
            <Route
              path="creator/products/:id/edit"
              element={
                <ProtectedRoute>
                  <CreatorProductEditor />
                </ProtectedRoute>
              }
            />
            <Route
              path="billing"
              element={
                <ProtectedRoute>
                  <Billing />
                </ProtectedRoute>
              }
            />
            <Route
              path="bridge"
              element={
                <ProtectedRoute>
                  <BridgeDevices />
                </ProtectedRoute>
              }
            />
            <Route
              path="workflows/:workflowId"
              element={
                <ProtectedRoute>
                  <Workflow />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
        </RouteErrorBoundary>
      </BrowserRouter>
    </AuthProvider>
  )
}