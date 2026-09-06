export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snacks'

export const MEAL_TYPES: MealType[] = ['breakfast', 'lunch', 'dinner', 'snacks']

export interface MealLogOut {
  id: string
  meal_type: MealType
  food_item_id: string | null
  food_name_snapshot: string | null
  quantity_g: number
  energy_kcal: number
  protein_g: number
  carb_g: number
  fat_g: number
  fibre_g: number | null
  notes: string | null
  source: 'user' | 'ai'
  logged_at: string
  created_at: string
}

export interface AddMealLinkedIn {
  food_item_id: string
  meal_type: MealType
  quantity_g: number
  logged_at?: string
  notes?: string
}

export interface AddMealFreeformIn {
  food_name_snapshot: string
  meal_type: MealType
  quantity_g: number
  energy_kcal: number
  protein_g?: number
  carb_g?: number
  fat_g?: number
  source?: 'user' | 'ai'
}

export type AddMealIn = AddMealLinkedIn | AddMealFreeformIn

export interface PatchMealIn {
  quantity_g?: number
  meal_type?: MealType
  logged_at?: string
  notes?: string
  energy_kcal?: number
  protein_g?: number
  carb_g?: number
  fat_g?: number
}
