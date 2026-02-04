import { api } from './api'
import type { AuthResponse, LoginCredentials } from '@/types'

export const login = async (data: LoginCredentials) => {
  const res = await api.post<AuthResponse>('/auth/login/', data)
  return res.data
}
