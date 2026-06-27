import type { BillingMeta, BillingTransaction } from '../types'

const TRIAL_CREDIT_TYPES = new Set(['signup_bonus', 'demo_topup', 'topup'])

export function isPlatformTestTransaction(tx: BillingTransaction): boolean {
  if (tx.billing_meta?.platform_tested || tx.billing_meta?.funding === 'platform_test') return true
  return tx.description.startsWith('Platform tested')
}

export function isTrialCreditTransaction(tx: BillingTransaction): boolean {
  return TRIAL_CREDIT_TYPES.has(tx.transaction_type)
}

export function isTrialUsageTransaction(tx: BillingTransaction): boolean {
  if (isPlatformTestTransaction(tx)) return false
  if (tx.transaction_type !== 'workflow_charge') return false
  if (tx.billing_meta?.funding === 'trial' || tx.billing_meta?.funding === 'mixed') return true
  return tx.description.includes('ทดลองใช้')
}

export function trialNoticeForTransaction(tx: BillingTransaction): string | null {
  if (isPlatformTestTransaction(tx)) return null
  if (tx.billing_meta?.trial_notice) return tx.billing_meta.trial_notice
  if (isTrialCreditTransaction(tx) || isTrialUsageTransaction(tx)) {
    return 'การทดลองใช้ — เจ้าของ agent ไม่ได้รับเงินจริง'
  }
  return null
}

export function platformNoticeForTransaction(tx: BillingTransaction): string | null {
  if (tx.billing_meta?.platform_notice) return tx.billing_meta.platform_notice
  if (isPlatformTestTransaction(tx)) {
    return 'ทดสอบโดยทีมแพลตฟอร์ม OBOLLA (Platform tested) — เจ้าของ agent ไม่ได้รับเงินจริง'
  }
  return null
}

export function fundingLabel(meta: BillingMeta | null | undefined): string | null {
  if (!meta) return null
  if (meta.funding === 'platform_test' || meta.platform_tested) return 'Platform tested'
  if (meta.funding === 'trial') return 'ทดลองใช้'
  if (meta.funding === 'mixed') return 'ทดลอง + จ่ายจริง'
  return null
}