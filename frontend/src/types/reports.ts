import type { GoalOut } from './goals'

export interface MacroTotals {
  energy_kcal: number
  protein_g: number
  carb_g: number
  fat_g: number
  fibre_g: number
}

export interface DailySummaryOut {
  date: string
  goal: GoalOut | null
  consumed: MacroTotals
  remaining: {
    energy_kcal: number
    protein_g: number
    carbs_g: number   // note: backend uses carbs_g here (not carb_g)
    fat_g: number
  } | null
  meals_tracked: number
}

export interface WeeklyDayEntry extends MacroTotals {
  date: string
}

export interface WeeklyReportOut {
  start: string
  end: string
  days_with_logs: number
  goal: GoalOut | null
  actual_period_avg: MacroTotals
  data: WeeklyDayEntry[]
  weight_logs: Array<{ logged_at: string; weight_kg: number }>
}

export interface MicrosReportOut {
  start: string
  end: string
  note: string
  totals: Record<string, number | null>
}
