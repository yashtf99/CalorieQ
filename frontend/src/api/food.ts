import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import type { FoodItemDetailOut, FoodItemSearchOut } from '@/types/food'
import type { PaginatedResponse } from '@/types/common'
import { apiClient } from './client'

interface FoodCategoryCount {
  category: string
  count: number
}

export function useFoodSearchInfinite(q: string, category?: string, enabled = true) {
  return useInfiniteQuery({
    queryKey: ['food-search-infinite', q, category],
    queryFn: ({ pageParam }) =>
      apiClient
        .get<PaginatedResponse<FoodItemSearchOut>>('/food_items', {
          params: { q, page_size: 10, page: pageParam, ...(category && { category }) },
        })
        .then((r) => ({
          data: r.data.data,
          total_pages: Math.ceil(r.data.meta.total / 10),
        })),
    initialPageParam: 1,
    getNextPageParam: (lastPage, allPages) =>
      allPages.length < lastPage.total_pages ? allPages.length + 1 : undefined,
    enabled: enabled && q.trim().length > 0,
    staleTime: 60_000,
  })
}

export function useFoodCategories(q: string, enabled = true) {
  return useQuery({
    queryKey: ['food-categories', q],
    queryFn: () =>
      apiClient
        .get<FoodCategoryCount[]>('/food_items/categories', { params: { q } })
        .then((r) => r.data),
    enabled: enabled && q.length > 0,
    staleTime: 60_000,
  })
}

export function useRecentFoods(limit = 5) {
  return useQuery({
    queryKey: ['recent-foods', limit],
    queryFn: () =>
      apiClient
        .get<FoodItemSearchOut[]>('/food_items/recent', { params: { limit } })
        .then((r) => r.data),
    staleTime: 30_000,
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
