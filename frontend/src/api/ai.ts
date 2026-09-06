import { useMutation } from '@tanstack/react-query'
import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

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
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)

      const token = useAuthStore.getState().accessToken
      const response = await axios.post<ImageExtractionResult>(
        `${import.meta.env.VITE_API_BASE_URL}/ai/extract_image`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            // Don't set Content-Type — let axios handle it for FormData
          },
        }
      )
      return response.data
    },
  })
}
