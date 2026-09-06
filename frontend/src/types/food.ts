export type FoodSource = 'indb' | 'usda' | 'user_custom'

export interface FoodItemSearchOut {
  id: string
  source: FoodSource
  name: string
  category: string | null
  energy_kcal: number
  protein_g: number
  carb_g: number
  fat_g: number
  fibre_g: number | null
}

export interface FoodPortion {
  id: string
  description: string
  gram_weight: number
}

// Full detail returned by GET /food_items/{id} — includes portions + all nutrients
export interface FoodItemDetailOut extends FoodItemSearchOut {
  is_verified: boolean
  portions: FoodPortion[]
  // Micronutrients (all nullable — not every food has full data)
  sodium_mg: number | null
  potassium_mg: number | null
  calcium_mg: number | null
  iron_mg: number | null
  vitc_mg: number | null
  vitd2_ug: number | null
  [key: string]: unknown  // remaining nutrient columns
}

// Scaled macros preview — computed on the frontend from per-100g values
export interface ScaledMacros {
  energy_kcal: number
  protein_g: number
  carb_g: number
  fat_g: number
  fibre_g: number | null
}

export function scaleMacros(food: FoodItemSearchOut, quantity_g: number): ScaledMacros {
  const ratio = quantity_g / 100
  return {
    energy_kcal: Math.round(food.energy_kcal * ratio),
    protein_g:   Math.round(food.protein_g   * ratio * 10) / 10,
    carb_g:      Math.round(food.carb_g      * ratio * 10) / 10,
    fat_g:       Math.round(food.fat_g       * ratio * 10) / 10,
    fibre_g:     food.fibre_g != null ? Math.round(food.fibre_g * ratio * 10) / 10 : null,
  }
}
