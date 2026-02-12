import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { User } from '@/types'

export default function Profile() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/users/me/')
      .then(res => setUser(res.data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading...</p>

  if (!user) return <p>Failed to load profile</p>

  return (
    <div>
      <h2>My Profile</h2>

      <p><b>Email:</b> {user.email}</p>
      <p><b>Username:</b> {user.username}</p>
      <p><b>Name:</b> {user.first_name} {user.last_name}</p>
      <p><b>Plan:</b> {user.subscription_tier}</p>
    </div>
  )
}
