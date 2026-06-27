export interface User {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Agent {
  id: string
  name: string
  description: string
  role: string
  llm_model: string
  tools: string[]
  is_active: boolean
  owner_id: string
  price_usd_per_run: string
  capabilities: string[]
  category: string | null
  created_at: string
  updated_at: string
  owner_name?: string | null
}

export interface AgentStats {
  portfolio_count: number
  total_hires: number
}

export interface PortfolioItem {
  id: string
  agent_id: string
  workflow_id: string
  title: string
  summary: string | null
  task_preview: string
  output_preview: string
  workflow_type: string
  is_public: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export interface AgentProfile {
  agent_id: string
  stats: AgentStats
  portfolio: PortfolioItem[]
}

export interface SkillShowcaseSkillSummary {
  id: string
  slug: string
  name: string
  category: string | null
  price_usd_per_run: string
}

export interface BotStatusChange {
  name: string
  before: string
  after: string
}

export interface ShowcaseBeforeAfter {
  score_before?: string | null
  score_after?: string | null
  bots: BotStatusChange[]
  fixes_applied: string[]
}

export interface SkillShowcase {
  id: string
  expert_skill_id: string
  title: string
  site_name: string
  site_url: string
  summary: string
  metric_label: string | null
  metric_value: string | null
  highlights: string[]
  sort_order: number
  is_featured: boolean
  is_active: boolean
  workflow_id: string | null
  sample_output: string | null
  deliverables: string[]
  stats: Record<string, string>
  before_after?: ShowcaseBeforeAfter
  created_at: string
  updated_at: string
  skill: SkillShowcaseSkillSummary | null
}

export interface SkillAttributionLink {
  label: string
  href: string
  detail: string
}

export interface SkillAttribution {
  charter_summary: string
  pack_slug: string
  upstream: SkillAttributionLink[]
  obolla_layer: string
  pricing_honesty: string
  credits_markdown?: string | null
}

export interface ModelTierRuntimeInfo {
  downgraded: boolean
  requested_tier_id?: string | null
  effective_tier_id?: string | null
  effective_price_usd?: string | null
  listed_price_usd?: string | null
  note_en?: string | null
  note_th?: string | null
}

export interface ExpertSkill {
  id: string
  slug: string
  name: string
  description: string
  i18n?: Record<string, { name?: string; description?: string }>
  display_locale?: 'th' | 'en' | null
  category: string | null
  pack_slug: string
  crew_config: Record<string, unknown>
  capabilities: string[]
  price_usd_per_run: string
  owner_id: string
  is_active: boolean
  created_at: string
  updated_at: string
  skill_preview?: string | null
  reference_count?: number
  owner_name?: string | null
  pipeline_steps?: PipelineStepInfo[]
  attribution?: SkillAttribution | null
  model_tier_runtime?: ModelTierRuntimeInfo | null
}

export interface CommunityLeaderboardEntry {
  owner_id: string
  owner_name: string
  flow_count: number
  earning_runs?: number
  categories: string[]
  featured_flow: {
    id: string
    name: string
    slug: string
    price_usd_per_run: string
  } | null
}

export interface CommunityVision {
  manifesto_th?: string
  manifesto_en?: string
  garden_story_th?: string[]
  garden_story_en?: string[]
  creator_garden_title_th?: string
  creator_garden_title_en?: string
  companion_th?: string
  companion_en?: string
  mission: string
  charter_rules: string[]
  charter_rules_th?: string[]
  dna: string[]
  dna_th?: string[]
}

export type DnaAuditStatus = 'pass' | 'fail' | 'warn'

export interface DnaAuditCheck {
  id: string
  dna_pillar: string
  claim_en: string
  claim_th: string
  status: DnaAuditStatus
  proved_by: string
  evidence: Record<string, unknown>
  detail_en?: string
  detail_th?: string
}

export interface DnaAuditReport {
  audited_at: string
  overall_status: DnaAuditStatus
  summary: {
    total: number
    passed: number
    failed: number
    warned: number
    dna_aligned: boolean
  }
  manifesto_th: string
  companion_th: string
  dna_th: string[]
  charter_rules_th: string[]
  checks: DnaAuditCheck[]
}

export interface CreatorGardenWorkflowIdea {
  name: string
  pitch: string
  steps: string
}

export interface GardenModelTier {
  id: string
  kind: 'llm' | 'local' | 'video'
  addon_usd: string
  suggested_price_usd: string
  label_en: string
  label_th: string
  engines_en: string
  engines_th: string
  hint_en: string
  hint_th: string
  available: boolean
  unavailable_reason_en: string | null
  unavailable_reason_th: string | null
}

export interface GardenModelTiersResponse {
  tiers: GardenModelTier[]
  base_price_usd: string
}

export interface CreatorGardenSuggestedDraft {
  identity?: string
  audience?: string
  problem?: string
  name?: string
  description?: string
  category?: string
  capabilities?: string[]
  input_mode?: string
  pipeline_label?: string
  run_title?: string
  skill_md?: string
  crew_config?: Record<string, unknown>
  model_tier_id?: string
  suggested_price_usd?: string
}

export interface CreatorGardenPdfImportMeta {
  filename: string
  page_count: number
  char_count: number
  summary_th?: string
  summary_en?: string
}

export interface PublishValueInsight {
  trend_signals_th: string[]
  trend_signals_en: string[]
  value_story_th: string
  value_story_en: string
  price_usd: string
  max_price_usd?: string
  pricing_ceiling_usd?: string
  value_score?: number
  value_tier?: 'starter' | 'growing' | 'strong' | 'premium' | string
  price_rationale_th: string
  price_rationale_en: string
  encouragement_th: string
  encouragement_en: string
  future_fit_th: string
  future_fit_en: string
  price_factors?: { key: string; th: string; en: string }[]
  base_price_usd?: string
  used_llm?: boolean
  composed?: boolean
}

export interface PublishReadinessMeta {
  test_run_at?: string
  test_workflow_id?: string
  passed?: boolean | null
  status?: string
  delivery_quality?: string | null
  task_preview?: string
  finalized_at?: string
}

export interface CreatorTestRunResponse {
  workflow_id: string
  status: string
  passed: boolean | null
  delivery_quality?: string | null
  message_th: string
  message_en: string
  skill?: ExpertSkill
}

export interface CreatorGardenCoachResponse {
  message_th: string
  message_en: string
  workflow_ideas: CreatorGardenWorkflowIdea[]
  suggested_draft: CreatorGardenSuggestedDraft
  value_insight?: PublishValueInsight
  companion_th: string
  composed?: boolean
  used_llm?: boolean
  model_tiers?: GardenModelTier[]
  pdf_import?: CreatorGardenPdfImportMeta | null
  error?: string
}

export interface PipelineStepInfo {
  id: string
  title: string
  step_type: string
  tool_or_model: string | null
}

export interface TokenResponse {
  access_token: string
  token_type: string
  is_new_user?: boolean
}

export interface WorkflowResponse {
  workflow_id: string
  status: string
  final_output: string | null
  total_tokens: number
  total_cost_usd: number
  execution_time_seconds: number | null
  error_message: string | null
  agent_id: string | null
  agents_used: string[] | null
  intermediate_results: Record<string, unknown> | null
  human_prompt: string | null
  workflow_type: string | null
  expert_skill_id: string | null
  billing: WorkflowBilling | null
}

export interface BuyerReviewItem {
  id: string
  expert_skill_id: string
  skill_name: string
  skill_slug: string
  rating: number
  comment: string
  status: string
  workflow_id: string | null
  created_at: string
  updated_at: string
  has_creator_reply: boolean
  unread_replies: number
}

export interface WorkflowReviewEligibility {
  eligible: boolean
  reason?: string | null
  workflow_id?: string | null
  workflow_status?: string | null
  expert_skill_id?: string | null
  skill_name?: string | null
  skill_slug?: string | null
  already_reviewed: boolean
  existing_review?: BuyerReviewItem | null
}

export interface BuyerReviewSubmitted {
  review: BuyerReviewItem
  message: string
}

export interface NotificationEvent {
  id: string
  event_type: 'new_review' | 'thread_reply' | 'thread_resolved' | string
  title: string
  body: string
  payload: Record<string, unknown>
  is_read: boolean
  created_at: string
}

export interface NotificationBadge {
  unread_count: number
}

export interface NotificationListResponse {
  items: NotificationEvent[]
  unread_count: number
}

export interface ToolInfo {
  name: string
  description: string
  source: string
}

export interface Wallet {
  user_id: string
  balance_usd: string
  earnings_balance_usd: string
  updated_at: string
}

export interface BillingConfig {
  stripe_enabled: boolean
  demo_topup_enabled: boolean
  platform_fee_percent: number
  signup_credits_usd: number
}

export interface CreatorEarning {
  id: string
  creator_id: string
  buyer_id: string
  agent_id: string
  product_type?: string
  workflow_id: string
  gross_amount_usd: string
  platform_fee_usd: string
  net_amount_usd: string
  created_at: string
}

export interface CustomTool {
  id: string
  name: string
  description: string
  tool_type: string
  config: Record<string, unknown>
  is_active: boolean
  owner_id: string
  created_at: string
  updated_at: string
}

export interface MCPServer {
  id: string
  name: string
  description: string
  transport: string
  config: Record<string, unknown>
  is_active: boolean
  owner_id: string
  created_at: string
  updated_at: string
}

export interface MCPTool {
  id: string
  mcp_server_id: string
  tool_name: string
  qualified_name: string
  description: string
  input_schema: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreatorSkillStats {
  total_runs: number
  total_earnings_usd: string
  average_rating: number | null
  review_count: number
}

export interface CreatorSkillItem extends ExpertSkill {
  stats: CreatorSkillStats
}

export interface CreatorTopSkill {
  skill_id: string
  skill_name: string
  runs: number
  earnings_usd: string
}

export interface CreatorActivityItem {
  id: string
  activity_type: string
  title: string
  detail: string | null
  amount_usd: string | null
  created_at: string
}

export interface CreatorSummary {
  total_earnings_usd: string
  earnings_balance_usd: string
  total_runs: number
  active_skills: number
  total_skills: number
  average_rating: number | null
  review_count: number
  top_skill_this_month: CreatorTopSkill | null
  recent_activity: CreatorActivityItem[]
  minimum_payout_usd: string
  platform_fee_percent: number
}

export interface AnalyticsDataPoint {
  period_start: string
  earnings_usd: string
  runs: number
}

export interface CreatorAnalytics {
  period: string
  data_points: AnalyticsDataPoint[]
  top_skills: CreatorTopSkill[]
  average_runs_per_day: number
  conversion_rate: number | null
  conversion_tracked: boolean
}

export interface SkillReview {
  id: string
  expert_skill_id: string
  skill_name: string
  buyer_id: string
  buyer_name: string
  rating: number
  comment: string
  workflow_id: string | null
  created_at: string
}

export interface CreatorReviewsSummary {
  average_rating: number | null
  review_count: number
  reviews: SkillReview[]
}

export interface ReviewInboxStats {
  average_rating: number | null
  total_reviews: number
  unread_count: number
  response_rate_percent: number
  average_response_time_hours: number | null
  average_response_time_label: string | null
}

export interface ReviewInboxItem {
  id: string
  expert_skill_id: string
  skill_name: string
  buyer_id: string
  buyer_name: string
  buyer_avatar_url: string | null
  rating: number
  comment_preview: string
  status: 'unread' | 'replied' | 'resolved'
  is_read: boolean
  workflow_id: string | null
  created_at: string
  updated_at: string
  first_response_at: string | null
  response_time_hours: number | null
  message_count: number
}

export interface ReviewInboxResponse {
  stats: ReviewInboxStats
  items: ReviewInboxItem[]
}

export interface ReviewAttachment {
  id: string
  file_name: string
  content_type: string
  file_size: number
  download_url: string
  created_at: string
}

export interface ThreadMessage {
  id: string
  sender_id: string
  sender_name: string
  sender_role: 'buyer' | 'creator'
  body: string
  attachments: ReviewAttachment[]
  created_at: string
  is_initial_review?: boolean
}

export interface ReviewThread {
  review_id: string
  expert_skill_id: string
  skill_name: string
  buyer_id: string
  buyer_name: string
  rating: number
  status: string
  messages: ThreadMessage[]
  first_response_at: string | null
  resolved_at: string | null
}

export interface QuickReply {
  id: string
  title: string
  body: string
  sort_order: number
  created_at: string
  updated_at: string
}

export interface ReviewNotificationSettings {
  notify_mode: 'all' | 'unread_only'
}

export interface ReviewNotificationBadge {
  unread_count: number
  notify_mode: string
}

export interface CreatorPayoutHistoryItem {
  id: string
  amount_usd: string
  transaction_type: string
  description: string
  created_at: string
}

export interface CreatorPayouts {
  earnings_balance_usd: string
  total_earned_usd: string
  minimum_payout_usd: string
  can_request_payout: boolean
  payout_history: CreatorPayoutHistoryItem[]
}

export interface EarningsSummary {
  earnings_balance_usd: string
  total_earned_usd: string
  platform_fee_percent: number
  recent_earnings: CreatorEarning[]
}

export interface AgentCharge {
  agent_id: string
  agent_name: string
  price_usd_per_run: string
}

export interface CostEstimate {
  marketplace_cost_usd: string
  estimated_llm_cost_usd: string
  estimated_total_usd: string
  agent_charges: AgentCharge[]
  current_balance_usd: string
  sufficient_balance: boolean
}

export interface BillingMeta {
  funding: string
  trial_amount_usd: string
  paid_amount_usd: string
  creator_payout_eligible: boolean
  platform_tested?: boolean
  trial_notice?: string | null
  trial_notice_en?: string | null
  platform_notice?: string | null
  platform_notice_en?: string | null
}

export interface WorkflowBilling {
  workflow_id: string
  marketplace_cost_usd: string
  llm_cost_usd: string
  total_charged_usd: string
  balance_after_usd: string | null
  charged: boolean
  creator_payouts?: CreatorEarning[]
  delivery_quality?: string | null
  marketplace_fee_multiplier?: number | null
  marketplace_waived_usd?: string | null
  trial_amount_usd?: string | null
  paid_amount_usd?: string | null
  creator_payout_eligible?: boolean | null
  trial_notice?: string | null
  platform_tested?: boolean | null
  platform_notice?: string | null
}

export interface BridgePairingCode {
  code: string
  expires_at: string
  expires_in_seconds: number
}

export interface BridgeDevice {
  id: string
  device_name: string
  capabilities: string[]
  allowed_roots: string[]
  last_seen_at: string | null
  created_at: string
}

export interface BridgeInvokeResult {
  ok: boolean
  result?: unknown
  error?: string
}

export interface BridgeConsentRequest {
  request_id: string
  device_id: string
  tool: string
  args: Record<string, unknown>
  created_at: string
}

export interface SmartFarmGatewayIp {
  ip: string
  label: string
  registered_at?: string
}

export interface SmartFarm {
  id: string
  name: string
  organization_name?: string | null
  address?: string | null
  latitude?: number | null
  longitude?: number | null
  google_maps_url?: string | null
  gateway_ips?: SmartFarmGatewayIp[]
  weather_alerts_enabled?: boolean
  mqtt_whitelist_hint?: string
  crop_type: string
  timezone: string
  auto_export_enabled: boolean
  auto_export_hours: number
  metadata: Record<string, unknown>
  created_at: string
  updated_at?: string | null
}

export interface SmartFarmWeatherAlert {
  level: 'medium' | 'high' | 'critical'
  type: string
  message: string
  date?: string
}

export interface SmartFarmWeatherResponse {
  farm_id: string
  weather: Record<string, unknown>
  alerts: SmartFarmWeatherAlert[]
}

export interface SmartFarmDevice {
  id: string
  device_name: string
  protocol: string
  mqtt_topic: string | null
  status: string
  last_seen_at: string | null
  created_at: string
  device_key?: string
  connect?: SmartFarmConnectKit
}

export interface SmartFarmConnectKit {
  recommended_transport?: 'https' | 'mqtt'
  http_ingest_url: string
  http_headers: Record<string, string>
  http_note?: string
  mqtt_topic: string
  mqtt_broker?: string
  mqtt_username?: string
  mqtt_password_hint?: string
  mqtt_tls?: boolean
  mqtt_broker_hint: string
  mqtt_note?: string
  sample_payload: Record<string, unknown>
  curl_example: string
}

export interface SmartFarmDatasetPack {
  id: string
  farm_id: string
  name: string
  format: string
  record_count: number
  window_start: string | null
  window_end: string | null
  status: string
  auto_generated: boolean
  download_url: string
  created_at: string
}

export interface SmartFarmDetail extends SmartFarm {
  devices: SmartFarmDevice[]
  datasets: SmartFarmDatasetPack[]
}

export interface BillingTransaction {
  id: string
  user_id: string
  workflow_id: string | null
  transaction_type: string
  amount_usd: string
  marketplace_cost_usd: string
  llm_cost_usd: string
  balance_after_usd: string
  description: string
  agent_charges: Record<string, unknown>[]
  billing_meta?: BillingMeta | null
  created_at: string
}