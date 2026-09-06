export type GoalType = 'lose' | 'maintain' | 'gain'
export type ActivityLevel = 'sedentary' | 'lightly_active' | 'active' | 'very_active'
export type Gender = 'male' | 'female' | 'other' | 'prefer_not_to_say'

export interface GoalSuggestionParams {
  height_cm: number
  weight_kg: number
  dob: string           // YYYY-MM-DD
  gender: Gender
  activity_level: ActivityLevel
}

export interface MacroSuggestion {
  daily_calories: number
  protein_g: number
  carbs_g: number
  fat_g: number
  fibre_g: number
}

export interface GoalSuggestionOut {
  bmr: number
  tdee: number
  suggestions: Record<GoalType, MacroSuggestion>
}

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
