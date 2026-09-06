export type GoalType = 'lose' | 'maintain' | 'gain'

export interface GoalOut {
  id: string
  goal_type: GoalType
  daily_calories: number | null
  protein_g: number | null
  carbs_g: number | null
  fat_g: number | null
  fibre_g: number | null
  weight_target_kg: number | null
  active_from: string
  active_to: string | null
}

export interface GoalIn {
  goal_type: GoalType
  daily_calories?: number
  protein_g?: number
  carbs_g?: number
  fat_g?: number
  fibre_g?: number
  weight_target_kg?: number
}
