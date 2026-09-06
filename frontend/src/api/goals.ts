import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import type { GoalIn, GoalOut, GoalSuggestionParams, GoalSuggestionOut } from '@/types/goals'
import type { PaginatedResponse } from '@/types/common'
import { apiClient } from './client'

export function useGoalSuggestion(params: GoalSuggestionParams | null) {
  return useQuery({
    queryKey: ['goal-suggestion', params],
    queryFn: () =>
      apiClient
        .get<GoalSuggestionOut>('/goals/suggest', { params: params! })
        .then((r) => r.data),
    enabled: params !== null,
    staleTime: 5 * 60_000,  // suggestions don't change within a session
  })
}

export function useActiveGoal() {
  return useQuery({
    queryKey: ['goal-active'],
    queryFn: () =>
      apiClient.get<GoalOut>('/goals/active').then((r) => r.data),
    // 404 means no goal set — treat as null, not an error
    retry: (_, error) => {
      const e = error as { response?: { status?: number } }
      return e?.response?.status !== 404
    },
  })
}

export function useGoalHistory() {
  return useQuery({
    queryKey: ['goal-history'],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<GoalOut>>('/goals/history')
        .then((r) => r.data),
  })
}

export function useCreateGoal() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: GoalIn) =>
      apiClient.post<GoalOut>('/goals', payload).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goal-active'] })
      queryClient.invalidateQueries({ queryKey: ['goal-history'] })
      // Daily summary and weekly report embed goal data — invalidate them too
      queryClient.invalidateQueries({ queryKey: ['daily-summary'] })
      queryClient.invalidateQueries({ queryKey: ['weekly-report'] })
      toast.success('Goals saved.')
    },
    onError: () => toast.error('Failed to save goals.'),
  })
}
