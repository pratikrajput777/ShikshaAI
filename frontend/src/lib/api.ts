import axios from 'axios'
import { config } from '@/config'

export const api = axios.create({
  baseURL: config.apiUrl,
  withCredentials: true,
  timeout: 20000,
})

api.interceptors.request.use((request) => {
  const token = localStorage.getItem('access_token')

  if (token) {
    request.headers.Authorization = `Bearer ${token}`
  }

  return request
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }

    return Promise.reject(error)
  }
)
