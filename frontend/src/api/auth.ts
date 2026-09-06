import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { useAuthStore } from '@/store/authStore'
import { apiClient } from './client'

type ApiError = { response?: { data?: { error?: { code?: string; message?: string } } } }

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  display_name: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user?: {
    id: string
    email: string
    display_name: string | null
    created_at: string
    updated_at: string
  }
}

function parseError(error: unknown): { code: string; message: string } {
  const e = error as ApiError
  return {
    code: e?.response?.data?.error?.code ?? 'UNKNOWN',
    message: e?.response?.data?.error?.message ?? '',
  }
}

export function useLogin() {
  const { setTokens } = useAuthStore()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: LoginRequest) =>
      apiClient.post<TokenResponse>('/auth/login', data).then((r) => r.data),
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token)
      navigate('/')
    },
    onError: (error) => {
      const { code, message } = parseError(error)
      if (code === 'USER_NOT_FOUND') {
        toast.error(message || 'No account found with that email.', {
          action: { label: 'Register', onClick: () => navigate('/register') },
        })
      } else {
        toast.error(message || 'Incorrect password.')
      }
    },
  })
}

export function useRegister() {
  const { setTokens } = useAuthStore()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: RegisterRequest) =>
      apiClient.post<TokenResponse>('/auth/register', data).then((r) => r.data),
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token, data.user)
      navigate('/')
    },
    onError: (error) => {
      const { message } = parseError(error)
      toast.error(message || 'Registration failed. Please try again.')
    },
  })
}

export function useLogout() {
  const { refreshToken, clearAuth } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () =>
      apiClient.post('/auth/logout', { refresh_token: refreshToken }).then((r) => r.data),
    onSettled: () => {
      clearAuth()
      queryClient.clear()
      navigate('/login')
    },
  })
}
