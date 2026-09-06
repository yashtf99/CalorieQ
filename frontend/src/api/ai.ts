import { useMutation } from '@tanstack/react-query'
import { apiClient } from './client'

export interface ImageExtractionResult {
  is_nutrition_label: boolean
  quantity_g?: number
  energy_kcal?: number
  protein_g?: number
  carb_g?: number
  fat_g?: number
  fibre_g?: number
  sodium_mg?: number
  food_item_name?: string
  confidence?: 'low' | 'medium' | 'high'
  estimation_basis?: string
}

export function useExtractImage() {
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      return apiClient
        .post<ImageExtractionResult>('/ai/extract_image', formData)
        .then((r) => r.data)
    },
  })
}
