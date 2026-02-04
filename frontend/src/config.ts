export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  stripePublicKey: import.meta.env.VITE_STRIPE_PUBLIC_KEY || '',
  googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
}
