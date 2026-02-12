import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
})

export interface LoginPayload {
  email: string
  password: string
}

export async function login(payload: LoginPayload) {
  const res = await api.post('/auth/login/', payload)
  return res.data
}
