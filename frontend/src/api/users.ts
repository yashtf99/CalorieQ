import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { useAuthStore } from '@/store/authStore'
import { apiClient } from './client'

export interface UserProfileOut {
  dob: string | null
  gender: string | null
  height_cm: number | null
  activity_level: string | null
  current_weight_kg: number | null
  updated_at: string | null
}

export interface UserProfilePatchIn {
  dob?: string
  gender?: string
  height_cm?: number
  activity_level?: string
  current_weight_kg?: number
}

export interface UserPatchIn {
  display_name?: string
}

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => apiClient.get('/users/me').then((r) => r.data),
  })
}

export function useProfile() {
  return useQuery({
    queryKey: ['profile'],
    queryFn: () => apiClient.get<UserProfileOut>('/users/me/profile').then((r) => r.data),
  })
}

export function usePatchProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: UserProfilePatchIn) =>
      apiClient.patch<UserProfileOut>('/users/me/profile', data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] })
    },
    onError: () => toast.error('Failed to save profile.'),
  })
}

export function usePatchMe() {
  const { setUser, user } = useAuthStore()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: UserPatchIn) =>
      apiClient.patch('/users/me', data).then((r) => r.data),
    onSuccess: (updated) => {
      setUser({ ...user!, ...updated })
      queryClient.invalidateQueries({ queryKey: ['me'] })
    },
    onError: () => toast.error('Failed to update profile.'),
  })
}
