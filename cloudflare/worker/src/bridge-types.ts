export type BridgeToolName = 
  | 'list_dir' 
  | 'read_file' 
  | 'write_file' 
  | 'run_command'
  | 'search_files'
  | 'get_file_info'
  | 'browse_page'           // browser control stub
  | 'run_local_llm'         // local LLM stub
  | 'execute_in_app'        // specific apps (e.g. vscode, excel)
  | 'get_local_network_info'  // for easy WiFi/Bluetooth detection
  | 'control_irrigation'      // for Eve Aqua etc.

export const BRIDGE_CONSENT_TOOLS: ReadonlySet<BridgeToolName> = new Set([
  'write_file',
  'run_command',
  'browse_page',
  'execute_in_app',
  'control_irrigation',
])

export type BridgeClientMessage =
  | { type: 'hello'; device_id: string; device_name: string }
  | { type: 'tool_result'; request_id: string; ok: boolean; result?: unknown; error?: string }
  | { type: 'pong' }

export type BridgeServerMessage =
  | { type: 'welcome'; device_id: string }
  | {
      type: 'tool_call'
      request_id: string
      tool: BridgeToolName
      args: Record<string, unknown>
      pre_approved?: boolean
    }
  | { type: 'consent_decision'; request_id: string; approved: boolean }
  | { type: 'ping' }

export type BridgeConsentRequest = {
  request_id: string
  device_id: string
  tool: BridgeToolName
  args: Record<string, unknown>
  created_at: string
}

export type BridgeDispatchRequest = {
  user_id: string
  device_id: string
  tool: BridgeToolName
  args: Record<string, unknown>
  timeout_ms?: number
}

export type BridgeDispatchResponse = {
  ok: boolean
  result?: unknown
  error?: string
}

export interface BridgeEnv {
  BACKEND_URL: string
  INTERNAL_BRIDGE_SECRET: string
  BRIDGE_HUB: DurableObjectNamespace
  NOTIFICATIONS_DB?: D1Database
}