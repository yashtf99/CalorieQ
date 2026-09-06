import { useQuery } from '@tanstack/react-query'
import type { FoodItemDetailOut, FoodItemSearchOut } from '@/types/food'
import type { PaginatedResponse } from '@/types/common'
import { apiClient } from './client'

export function useFoodSearch(q: string, enabled = true) {
  return useQuery({
    queryKey: ['food-search', q],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<FoodItemSearchOut>>('/food_items', {
          params: { q, page_size: 10 },
        })
        .then((r) => r.data.data),
    enabled: enabled && q.trim().length > 0,
    staleTime: 60_000,  // food db doesn't change — cache aggressively
  })
}

export function useFoodItem(id: string | null) {
  return useQuery({
    queryKey: ['food-item', id],
    queryFn: () =>
      apiClient.get<FoodItemDetailOut>(`/food_items/${id}`).then((r) => r.data),
    enabled: !!id,
    staleTime: 60_000,
  })
}
