import type {
  Agent,
  AgentProfile,
  BillingConfig,
  PortfolioItem,
  BillingTransaction,
  CostEstimate,
  CreatorAnalytics,
  CreatorPayouts,
  CreatorReviewsSummary,
  QuickReply,
  BuyerReviewItem,
  BuyerReviewSubmitted,
  NotificationBadge,
  NotificationListResponse,
  ReviewInboxResponse,
  ReviewNotificationBadge,
  ReviewNotificationSettings,
  ReviewThread,
  ThreadMessage,
  WorkflowReviewEligibility,
  CreatorSkillItem,
  CreatorSummary,
  CustomTool,
  ExpertSkill,
  MCPServer,
  MCPTool,
  SkillShowcase,
  EarningsSummary,
  TokenResponse,
  ToolInfo,
  User,
  Wallet,
  WorkflowResponse,
  BridgePairingCode,
  BridgeConsentRequest,
  BridgeDevice,
  BridgeInvokeResult,
  SmartFarm,
  SmartFarmDatasetPack,
  SmartFarmDetail,
  SmartFarmDevice,
} from '../types'

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api/v1'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// request is now exported above

export function apiErrorMessage(err: unknown, locale: 'th' | 'en' = 'en'): string {
  if (!(err instanceof ApiError)) {
    return err instanceof Error ? err.message : locale === 'th' ? 'เกิดข้อผิดพลาด' : 'Something went wrong'
  }
  const msg = err.message.toLowerCase()
  const backendDown =
    err.status === 502 ||
    err.status === 503 ||
    msg.includes('tunnel') ||
    msg.includes('unreachable') ||
    msg.includes('backend api')
  if (backendDown) {
    return locale === 'th'
      ? 'เซิร์ฟเวอร์ยังไม่พร้อมชั่วคราว — รอ 1–2 นาทีแล้วกดสร้างอีกครั้ง'
      : 'Server is temporarily unavailable — wait a minute and try again.'
  }
  if (err.status === 401) {
    return locale === 'th' ? 'กรุณาเข้าสู่ระบบก่อน' : 'Please sign in first.'
  }
  return err.message
}

export async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers)
  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!response.ok) {
    let detail = response.statusText
    try {
      const payload = await response.json()
      detail = payload.detail ?? JSON.stringify(payload)
    } catch {
      // ignore parse errors
    }
    throw new ApiError(response.status, String(detail))
  }

  if (response.status === 204) {
    return undefined as T
  }
  return response.json() as Promise<T>
}

async function requestMultipart<T>(
  path: string,
  formData: FormData,
  token: string,
): Promise<T> {
  const headers = new Headers()
  headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_BASE}${path}`, { method: 'POST', headers, body: formData })
  if (!response.ok) {
    let detail = response.statusText
    try {
      const payload = await response.json()
      detail = payload.detail ?? JSON.stringify(payload)
    } catch {
      // ignore
    }
    throw new ApiError(response.status, String(detail))
  }
  return response.json() as Promise<T>
}

export const api = {
  register: (email: string, password: string, full_name: string) =>
    request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  loginWithGoogle: (id_token: string) =>
    request<TokenResponse>('/auth/google', {
      method: 'POST',
      body: JSON.stringify({ id_token }),
    }),

  me: (token: string) => request<User>('/auth/me', {}, token),

  listExpertSkills: (category?: string, lang?: string) => {
    const query = new URLSearchParams()
    if (category) query.set('category', category)
    if (lang) query.set('lang', lang)
    const suffix = query.toString() ? `?${query}` : ''
    return request<ExpertSkill[]>(`/expert-skills${suffix}`)
  },

  getExpertSkill: (id: string, lang?: string) => {
    const suffix = lang ? `?lang=${encodeURIComponent(lang)}` : ''
    return request<ExpertSkill>(`/expert-skills/${id}${suffix}`)
  },

  listShowcases: (params?: {
    category?: string
    expert_skill_id?: string
    featured_only?: boolean
  }) => {
    const query = new URLSearchParams()
    if (params?.category) query.set('category', params.category)
    if (params?.expert_skill_id) query.set('expert_skill_id', params.expert_skill_id)
    if (params?.featured_only) query.set('featured_only', 'true')
    const suffix = query.toString() ? `?${query}` : ''
    return request<SkillShowcase[]>(`/showcases${suffix}`)
  },

  getCommunityVision: () => request<import('../types').CommunityVision>('/community/vision'),

  getDnaAudit: () => request<import('../types').DnaAuditReport>('/community/dna-audit'),

  getCommunityLeaderboard: () =>
    request<import('../types').CommunityLeaderboardEntry[]>('/community/leaderboard'),

  creatorGardenCoach: (payload: { step: string; answers?: Record<string, string> }) =>
    request<import('../types').CreatorGardenCoachResponse>('/community/creator-garden/coach', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getGardenModelTiers: () =>
    request<import('../types').GardenModelTiersResponse>('/community/creator-garden/model-tiers'),

  creatorGardenCompose: async (payload: {
    raw_story: string
    locale?: string
    model_tier_id?: string
  }) => {
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 90_000)
    try {
      const response = await fetch(`${API_BASE}/community/creator-garden/compose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      })
      if (!response.ok) {
        let detail = response.statusText
        try {
          const body = await response.json()
          detail = body.detail ?? JSON.stringify(body)
        } catch {
          // ignore
        }
        throw new ApiError(response.status, String(detail))
      }
      return response.json() as Promise<import('../types').CreatorGardenCoachResponse>
    } finally {
      window.clearTimeout(timeout)
    }
  },

  creatorGardenImportPdf: async (file: File, locale?: string, model_tier_id?: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('locale', locale ?? 'th')
    form.append('model_tier_id', model_tier_id ?? 'standard')
    const response = await fetch(`${API_BASE}/community/creator-garden/import-pdf`, {
      method: 'POST',
      body: form,
    })
    if (!response.ok) {
      let detail = response.statusText
      try {
        const payload = await response.json()
        detail = payload.detail ?? payload.error ?? JSON.stringify(payload)
      } catch {
        // ignore
      }
      throw new ApiError(response.status, String(detail))
    }
    return response.json() as Promise<import('../types').CreatorGardenCoachResponse>
  },

  creatorGardenApplyTier: (payload: { model_tier_id: string; crew_config: Record<string, unknown> }) =>
    request<{
      model_tier_id: string
      suggested_price_usd: string
      pipeline_label?: string
      crew_config: Record<string, unknown>
    }>('/community/creator-garden/apply-tier', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  creatorGardenValueInsight: (payload: {
    raw_story?: string
    locale?: string
    workflow_name: string
    description?: string
    category?: string
    identity?: string
    audience?: string
    problem?: string
    model_tier_id?: string
  }) =>
    request<import('../types').PublishValueInsight>('/community/creator-garden/value-insight', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  creatorSkillTestRun: (token: string, skillId: string) =>
    request<import('../types').CreatorTestRunResponse>(
      `/creators/me/skills/${skillId}/test-run`,
      { method: 'POST' },
      token,
    ),

  finalizeCreatorTestRun: (token: string, skillId: string, workflowId: string) =>
    request<import('../types').CreatorTestRunResponse>(
      `/creators/me/skills/${skillId}/test-run/finalize`,
      { method: 'POST', body: JSON.stringify({ workflow_id: workflowId }) },
      token,
    ),

  createShowcaseFromWorkflow: (
    token: string,
    payload: { workflow_id: string; title?: string; site_name?: string; site_url?: string },
  ) =>
    request<SkillShowcase>(
      '/creators/me/showcases/from-workflow',
      { method: 'POST', body: JSON.stringify(payload) },
      token,
    ),

  getShowcase: (id: string) => request<SkillShowcase>(`/showcases/${id}`),

  listMarketplaceAgents: (params?: { category?: string; max_price?: string }) => {
    const query = new URLSearchParams()
    if (params?.category) query.set('category', params.category)
    if (params?.max_price) query.set('max_price', params.max_price)
    const suffix = query.toString() ? `?${query}` : ''
    return request<Agent[]>(`/marketplace/agents${suffix}`)
  },

  listAgents: (token: string) => request<Agent[]>('/agents', {}, token),

  getAgent: (id: string) => request<Agent>(`/agents/${id}`),

  getAgentProfile: (id: string, token?: string | null, includePrivate = false) => {
    const query = includePrivate ? '?include_private=true' : ''
    return request<AgentProfile>(`/agents/${id}/profile${query}`, {}, token)
  },

  addPortfolioItem: (
    token: string,
    agentId: string,
    payload: { workflow_id: string; title?: string; summary?: string; is_public?: boolean },
  ) =>
    request<PortfolioItem>(
      `/agents/${agentId}/portfolio`,
      { method: 'POST', body: JSON.stringify(payload) },
      token,
    ),

  deletePortfolioItem: (token: string, agentId: string, itemId: string) =>
    request<void>(`/agents/${agentId}/portfolio/${itemId}`, { method: 'DELETE' }, token),

  createAgent: (token: string, payload: Record<string, unknown>) =>
    request<Agent>('/agents', { method: 'POST', body: JSON.stringify(payload) }, token),

  updateAgent: (token: string, id: string, payload: Record<string, unknown>) =>
    request<Agent>(`/agents/${id}`, { method: 'PUT', body: JSON.stringify(payload) }, token),

  deleteAgent: (token: string, id: string) =>
    request<void>(`/agents/${id}`, { method: 'DELETE' }, token),

  listTools: () => request<ToolInfo[]>('/tools'),

  runWorkflow: (
    token: string,
    payload: {
      task_description: string
      workflow_type?: string
      agent_id?: string
      agents?: string[]
      expert_skill_id?: string
      require_human_approval?: boolean
      bridge_device_id?: string
      task_context?: Record<string, unknown>
    },
  ) =>
    request<WorkflowResponse>('/workflows/run', { method: 'POST', body: JSON.stringify(payload) }, token),

  getWorkflow: (token: string, workflowId: string) =>
    request<WorkflowResponse>(`/workflows/${workflowId}`, {}, token),

  resumeWorkflow: (token: string, workflowId: string, feedback: string) =>
    request<WorkflowResponse>(
      `/workflows/${workflowId}/resume`,
      { method: 'POST', body: JSON.stringify({ feedback }) },
      token,
    ),

  getBillingConfig: () => request<BillingConfig>('/billing/config'),

  getWallet: (token: string) => request<Wallet>('/billing/wallet', {}, token),

  getEarnings: (token: string) => request<EarningsSummary>('/billing/earnings', {}, token),

  listTransactions: (token: string) =>
    request<BillingTransaction[]>('/billing/transactions', {}, token),

  estimateCost: (
    token: string,
    payload: {
      workflow_type?: string
      agent_id?: string
      agents?: string[]
      expert_skill_id?: string
    },
  ) =>
    request<CostEstimate>('/billing/estimate', { method: 'POST', body: JSON.stringify(payload) }, token),

  topUp: (token: string, amount_usd: string) =>
    request<Wallet>('/billing/topup', { method: 'POST', body: JSON.stringify({ amount_usd }) }, token),

  createStripeCheckout: (token: string, amount_usd: string) =>
    request<{ checkout_url: string; session_id: string }>(
      '/billing/stripe/checkout',
      { method: 'POST', body: JSON.stringify({ amount_usd }) },
      token,
    ),

  transferEarnings: (token: string, amount_usd?: string) =>
    request<Wallet>(
      '/billing/earnings/transfer',
      { method: 'POST', body: JSON.stringify(amount_usd ? { amount_usd } : {}) },
      token,
    ),

  getCreatorSummary: (token: string) =>
    request<CreatorSummary>('/creators/me/summary', {}, token),

  getCreatorSkills: (token: string) =>
    request<CreatorSkillItem[]>('/creators/me/skills', {}, token),

  createCreatorSkill: (
    token: string,
    payload: {
      name: string
      slug: string
      description: string
      category?: string
      price_usd_per_run: string
    },
  ) =>
    request<ExpertSkill>('/creators/me/skills', { method: 'POST', body: JSON.stringify(payload) }, token),

  updateCreatorSkill: (
    token: string,
    skillId: string,
    payload: {
      name?: string
      description?: string
      name_th?: string
      description_th?: string
      category?: string
      price_usd_per_run?: string
      is_active?: boolean
      capabilities?: string[]
      crew_config?: Record<string, unknown>
    },
  ) =>
    request<ExpertSkill>(`/creators/me/skills/${skillId}`, { method: 'PATCH', body: JSON.stringify(payload) }, token),

  deleteCreatorSkill: (token: string, skillId: string) =>
    request<void>(`/creators/me/skills/${skillId}`, { method: 'DELETE' }, token),

  getCreatorAnalytics: (token: string, period: 'day' | 'week' | 'month' = 'week') =>
    request<CreatorAnalytics>(`/creators/me/analytics?period=${period}`, {}, token),

  getCreatorPayouts: (token: string) =>
    request<CreatorPayouts>('/creators/me/payouts', {}, token),

  getCreatorReviews: (token: string) =>
    request<CreatorReviewsSummary>('/creators/me/reviews', {}, token),

  // PM-approved: Moat Intelligence (Revenue Attribution + Agent Behavior signals)
  getMoatIntelligence: (url: string, token?: string) =>
    request<any>(`/moat/intelligence?url=${encodeURIComponent(url)}`, {}, token),
  getRevenueIntelligence: (skillSlug?: string, token?: string) =>
    request<any>(`/moat/revenue-intelligence${skillSlug ? `?skill_slug=${skillSlug}` : ''}`, {}, token),
  getRevenueOutreach: (skillSlug: string, token?: string) =>
    request<any>(`/moat/revenue-outreach?skill_slug=${skillSlug}`, {}, token),
  executeRevenueOutreach: (skillSlug: string, templateIndex: number = 0, token?: string) =>
    request<any>(`/moat/revenue-outreach/execute?skill_slug=${skillSlug}&template_index=${templateIndex}`, { method: 'POST' }, token),
  logRevenueSale: (skillSlug: string, amountUsd: number, loggedId?: string, token?: string) =>
    request<any>(`/moat/revenue-sale/log?skill_slug=${skillSlug}&amount_usd=${amountUsd}${loggedId ? `&logged_id=${loggedId}` : ''}`, { method: 'POST' }, token),
  getRevenuePipeline: (skillSlug: string, token?: string) =>
    request<any>(`/moat/revenue-pipeline?skill_slug=${skillSlug}`, {}, token),
  logRevenueOutreach: (skillSlug: string, amountUsd: number, note?: string, token?: string) =>
    request<any>(`/moat/revenue-outreach/log?skill_slug=${skillSlug}&amount_usd=${amountUsd}&note=${encodeURIComponent(note || 'outreach lead')}`, { method: 'POST' }, token),
  getProprietaryValidation: (skillSlug?: string, token?: string) =>
    request<any>(`/moat/proprietary-validation${skillSlug ? `?skill_slug=${skillSlug}` : ''}`, {}, token),
  runBatchValidation: (token?: string) =>
    request<any>(`/moat/proprietary-validation/run-batch`, { method: 'POST' }, token),

  getCreatorTools: (token: string) =>
    request<CustomTool[]>('/creators/me/tools', {}, token),

  getCreatorMcpServers: (token: string) =>
    request<MCPServer[]>('/creators/me/mcp-servers', {}, token),

  listCustomTools: (ownerId: string) =>
    request<CustomTool[]>(`/custom-tools?owner_id=${encodeURIComponent(ownerId)}&active_only=false`),

  listMcpServers: (ownerId: string) =>
    request<MCPServer[]>(`/mcp-servers?owner_id=${encodeURIComponent(ownerId)}&active_only=false`),

  createCustomTool: (
    token: string,
    payload: {
      name: string
      description: string
      tool_type: 'http'
      config: Record<string, unknown>
      is_active?: boolean
    },
  ) =>
    request<CustomTool>('/custom-tools', { method: 'POST', body: JSON.stringify(payload) }, token),

  updateCustomTool: (
    token: string,
    toolId: string,
    payload: { description?: string; config?: Record<string, unknown>; is_active?: boolean },
  ) =>
    request<CustomTool>(`/custom-tools/${toolId}`, { method: 'PUT', body: JSON.stringify(payload) }, token),

  deleteCustomTool: (token: string, toolId: string) =>
    request<void>(`/custom-tools/${toolId}`, { method: 'DELETE' }, token),

  createMcpServer: (
    token: string,
    payload: {
      name: string
      description: string
      transport: 'http' | 'sse' | 'stdio'
      config: Record<string, unknown>
      is_active?: boolean
    },
  ) =>
    request<MCPServer>('/mcp-servers', { method: 'POST', body: JSON.stringify(payload) }, token),

  updateMcpServer: (
    token: string,
    serverId: string,
    payload: {
      description?: string
      transport?: 'http' | 'sse' | 'stdio'
      config?: Record<string, unknown>
      is_active?: boolean
    },
  ) =>
    request<MCPServer>(`/mcp-servers/${serverId}`, { method: 'PUT', body: JSON.stringify(payload) }, token),

  deleteMcpServer: (token: string, serverId: string) =>
    request<void>(`/mcp-servers/${serverId}`, { method: 'DELETE' }, token),

  syncMcpServerTools: (token: string, serverId: string) =>
    request<MCPTool[]>(`/mcp-servers/${serverId}/sync-tools`, { method: 'POST' }, token),

  listMcpServerTools: (token: string, serverId: string, activeOnly = false) =>
    request<MCPTool[]>(
      `/mcp-servers/${serverId}/tools?active_only=${activeOnly}`,
      {},
      token,
    ),

  getReviewInbox: (
    token: string,
    params?: {
      status?: string
      rating?: number
      search?: string
      sort?: 'newest' | 'unanswered' | 'response_time'
    },
  ) => {
    const query = new URLSearchParams()
    if (params?.status) query.set('status', params.status)
    if (params?.rating) query.set('rating', String(params.rating))
    if (params?.search) query.set('search', params.search)
    if (params?.sort) query.set('sort', params.sort)
    const suffix = query.toString() ? `?${query}` : ''
    return request<ReviewInboxResponse>(`/creators/me/reviews/inbox${suffix}`, {}, token)
  },

  getReviewInboxBadge: (token: string) =>
    request<ReviewNotificationBadge>('/creators/me/reviews/inbox/badge', {}, token),

  getReviewThread: (token: string, reviewId: string) =>
    request<ReviewThread>(`/creators/me/reviews/${reviewId}/thread`, {}, token),

  replyToReview: (token: string, reviewId: string, body: string, files: File[] = []) => {
    const form = new FormData()
    form.append('body', body)
    files.forEach((file) => form.append('files', file))
    return requestMultipart<ThreadMessage>(`/creators/me/reviews/${reviewId}/reply`, form, token)
  },

  resolveReview: (token: string, reviewId: string) =>
    request<{ ok: boolean }>(`/creators/me/reviews/${reviewId}/resolve`, { method: 'POST' }, token),

  getQuickReplies: (token: string) =>
    request<QuickReply[]>('/creators/me/reviews/quick-replies', {}, token),

  createQuickReply: (token: string, payload: { title: string; body: string }) =>
    request<QuickReply>('/creators/me/reviews/quick-replies', { method: 'POST', body: JSON.stringify(payload) }, token),

  updateQuickReply: (token: string, replyId: string, payload: { title?: string; body?: string }) =>
    request<QuickReply>(`/creators/me/reviews/quick-replies/${replyId}`, { method: 'PATCH', body: JSON.stringify(payload) }, token),

  deleteQuickReply: (token: string, replyId: string) =>
    request<void>(`/creators/me/reviews/quick-replies/${replyId}`, { method: 'DELETE' }, token),

  getReviewNotificationSettings: (token: string) =>
    request<ReviewNotificationSettings>('/creators/me/reviews/notification-settings', {}, token),

  updateReviewNotificationSettings: (token: string, notify_mode: 'all' | 'unread_only') =>
    request<ReviewNotificationSettings>(
      '/creators/me/reviews/notification-settings',
      { method: 'PUT', body: JSON.stringify({ notify_mode }) },
      token,
    ),

  getWorkflowReviewEligibility: (token: string, workflowId: string) =>
    request<WorkflowReviewEligibility>(`/reviews/me/workflow/${workflowId}/eligibility`, {}, token),

  submitBuyerReview: (
    token: string,
    payload: { workflow_id: string; expert_skill_id: string; rating: number; comment: string },
  ) =>
    request<BuyerReviewSubmitted>('/reviews/me', { method: 'POST', body: JSON.stringify(payload) }, token),

  listBuyerReviews: (token: string) => request<BuyerReviewItem[]>('/reviews/me', {}, token),

  getBuyerReviewThread: (token: string, reviewId: string) =>
    request<ReviewThread>(`/reviews/me/${reviewId}/thread`, {}, token),

  replyAsBuyer: (token: string, reviewId: string, body: string) => {
    const form = new FormData()
    form.append('body', body)
    return requestMultipart<ThreadMessage>(`/reviews/me/${reviewId}/reply`, form, token)
  },

  getNotificationBadge: (token: string) =>
    request<NotificationBadge>('/notifications/badge', {}, token),

  getNotifications: (token: string, limit = 30) =>
    request<NotificationListResponse>(`/notifications?limit=${limit}`, {}, token),

  markNotificationsRead: (token: string, ids?: string[]) =>
    request<NotificationBadge>(
      '/notifications/mark-read',
      { method: 'POST', body: JSON.stringify({ ids: ids ?? [] }) },
      token,
    ),

  createBridgePairingCode: (token: string) =>
    request<BridgePairingCode>('/bridge/pairing-codes', { method: 'POST' }, token),

  listBridgeDevices: (token: string) => request<BridgeDevice[]>('/bridge/devices', {}, token),

  revokeBridgeDevice: (token: string, deviceId: string) =>
    request<void>(`/bridge/devices/${deviceId}`, { method: 'DELETE' }, token),

  invokeBridgeTool: (
    token: string,
    deviceId: string,
    payload: { tool: string; args: Record<string, unknown> },
  ) =>
    request<BridgeInvokeResult>(
      `/bridge/devices/${deviceId}/invoke`,
      { method: 'POST', body: JSON.stringify(payload) },
      token,
    ),

  listBridgeConsentPending: (token: string) =>
    request<{ items: BridgeConsentRequest[] }>('/bridge/consent/pending', {}, token),

  respondBridgeConsent: (token: string, requestId: string, approved: boolean) =>
    request<{ ok: boolean }>(
      `/bridge/consent/${requestId}/respond`,
      { method: 'POST', body: JSON.stringify({ approved }) },
      token,
    ),

  getBridgeDeviceOnline: (token: string, deviceId: string) =>
    request<{ online: boolean }>(`/bridge/devices/${deviceId}/online`, {}, token),

  transcribeSpeech: async (
    audio: Blob,
    lang: string,
    filename = 'speech.webm',
    signal?: AbortSignal,
  ) => {
    const form = new FormData()
    form.append('audio', audio, filename)
    form.append('lang', lang)
    const response = await fetch(`${API_BASE}/speech/transcribe`, {
      method: 'POST',
      body: form,
      signal,
    })
    if (!response.ok) {
      let detail = response.statusText
      try {
        const payload = await response.json()
        detail = payload.detail ?? JSON.stringify(payload)
      } catch {
        // ignore
      }
      throw new ApiError(response.status, String(detail))
    }
    return response.json() as Promise<{ text: string }>
  },

  listSmartFarms: (token: string) =>
    request<SmartFarm[]>('/smart-farm/farms', {}, token),

  createSmartFarm: (
    token: string,
    body: {
      name: string
      organization_name?: string
      address?: string
      latitude?: number
      longitude?: number
      google_maps_url?: string
      gateway_ips?: { ip: string; label: string }[]
      weather_alerts_enabled?: boolean
      crop_type?: string
    },
  ) => request<SmartFarm>('/smart-farm/farms', { method: 'POST', body: JSON.stringify(body) }, token),

  updateSmartFarm: (
    token: string,
    farmId: string,
    body: Record<string, unknown>,
  ) => request<SmartFarm>(`/smart-farm/farms/${farmId}`, { method: 'PUT', body: JSON.stringify(body) }, token),

  geocodeSmartFarmAddress: (token: string, address: string) =>
    request<{
      latitude: number
      longitude: number
      display_name: string
      google_maps_url: string
      openstreetmap_url: string
    }>('/smart-farm/geocode', { method: 'POST', body: JSON.stringify({ address }) }, token),

  getSmartFarmWeather: (token: string, farmId: string) =>
    request<import('../types').SmartFarmWeatherResponse>(`/smart-farm/farms/${farmId}/weather`, {}, token),

  getSmartFarm: (token: string, farmId: string) =>
    request<SmartFarmDetail>(`/smart-farm/farms/${farmId}`, {}, token),

  createSmartFarmDevice: (token: string, farmId: string, body: { device_name: string; protocol?: string }) =>
    request<SmartFarmDevice>(`/smart-farm/farms/${farmId}/devices`, { method: 'POST', body: JSON.stringify(body) }, token),

  exportSmartFarmDataset: (token: string, farmId: string, body: { name?: string; format?: string; hours?: number }) =>
    request<SmartFarmDatasetPack>(`/smart-farm/farms/${farmId}/datasets/export`, { method: 'POST', body: JSON.stringify(body) }, token),

  uploadSmartFarmFile: async (token: string, farmId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    const response = await fetch(`${API_BASE}/smart-farm/farms/${farmId}/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    })
    if (!response.ok) {
      let detail = response.statusText
      try {
        const payload = await response.json()
        detail = payload.detail ?? JSON.stringify(payload)
      } catch {
        // ignore
      }
      throw new ApiError(response.status, String(detail))
    }
    return response.json() as Promise<{ ok: boolean; readings_ingested: number }>
  },

  downloadSmartFarmDataset: async (token: string, packId: string, fileName: string) => {
    const response = await fetch(`${API_BASE}/smart-farm/datasets/${packId}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) throw new ApiError(response.status, 'Download failed')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = fileName
    anchor.click()
    URL.revokeObjectURL(url)
  },

  getSmartFarmCropSchema: (cropType: string) =>
    request<Record<string, unknown>>(`/smart-farm/schema/${cropType}`),

  downloadReviewAttachment: async (token: string, attachmentId: string, fileName: string) => {
    const response = await fetch(`${API_BASE}/creators/me/reviews/attachments/${attachmentId}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) throw new ApiError(response.status, 'Download failed')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = fileName
    anchor.click()
    URL.revokeObjectURL(url)
  },
}