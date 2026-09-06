import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { USER_TZ } from '@/lib/tz'
import type { AddMealIn, MealLogOut, PatchMealIn } from '@/types/meals'
import type { PaginatedResponse } from '@/types/common'
import { apiClient } from './client'

export function useMealHistory(date: string) {
  return useQuery({
    queryKey: ['meals', date, USER_TZ],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<MealLogOut>>('/meals/history', {
          params: { date, tz: USER_TZ, page_size: 100 },
        })
        .then((r) => r.data.data),  // unwrap paginated envelope → flat array
  })
}

export function useAddMeal(date: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: AddMealIn) =>
      apiClient.post<MealLogOut>('/meals', payload).then((r) => r.data),
    onSuccess: () => {
      // Invalidate both the meal list and the daily summary so ring + bars update instantly
      queryClient.invalidateQueries({ queryKey: ['meals', date] })
      queryClient.invalidateQueries({ queryKey: ['daily-summary', date] })
    },
    onError: () => toast.error('Failed to add meal. Please try again.'),
  })
}

export function useDeleteMeal(date: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/meals/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meals', date] })
      queryClient.invalidateQueries({ queryKey: ['daily-summary', date] })
    },
    onError: () => toast.error('Failed to delete meal.'),
  })
}

export function useUpdateMeal(date: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: PatchMealIn }) =>
      apiClient.patch<MealLogOut>(`/meals/${id}`, patch).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meals', date] })
      queryClient.invalidateQueries({ queryKey: ['daily-summary', date] })
    },
    onError: () => toast.error('Failed to update meal.'),
  })
}
