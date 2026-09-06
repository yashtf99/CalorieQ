import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
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

const SUPPORTED_FORMATS = ['image/jpeg', 'image/png', 'image/jpg', 'image/bmp', 'image/tiff', 'image/webp']

export function useExtractImage() {
  return useMutation({
    mutationFn: async (file: File) => {
      // Validate file format
      if (!SUPPORTED_FORMATS.includes(file.type)) {
        throw new Error(`Unsupported image format: ${file.type || 'unknown'}. Please use JPEG, PNG, BMP, TIFF, or WebP.`)
      }

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
    onError: (error) => {
      const message = error instanceof Error ? error.message : 'Failed to extract nutrition from image'
      toast.error(message)
    },
  })
}
