import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/store/authStore'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL as string,
  headers: { 'Content-Type': 'application/json' },
})

// Attach access token to every request
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let isRefreshing = false
let refreshQueue: Array<(token: string) => void> = []

// On 401: refresh → retry; on second 401: clear auth + redirect
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config

    const isAuthEndpoint = original.url?.includes('/auth/')
    if (error.response?.status !== 401 || original._retry || isAuthEndpoint) {
      return Promise.reject(error)
    }

    const { refreshToken, setTokens, clearAuth } = useAuthStore.getState()
    if (!refreshToken) {
      clearAuth()
      window.location.href = '/login'
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve) => {
        refreshQueue.push((token: string) => {
          original.headers.Authorization = `Bearer ${token}`
          resolve(apiClient(original))
        })
      })
    }

    original._retry = true
    isRefreshing = true

    try {
      const { data } = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/auth/refresh`,
        { refresh_token: refreshToken },
      )
      const newAccess: string = data.access_token
      const newRefresh: string = data.refresh_token
      setTokens(newAccess, newRefresh)
      refreshQueue.forEach((cb) => cb(newAccess))
      refreshQueue = []
      original.headers.Authorization = `Bearer ${newAccess}`
      return apiClient(original)
    } catch {
      clearAuth()
      window.location.href = '/login'
      return Promise.reject(error)
    } finally {
      isRefreshing = false
    }
  },
)
