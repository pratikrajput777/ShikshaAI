/*import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'


function App() {
  return (
    <div style={{ padding: 40 }}>
      <Button>Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button loading>Loading</Button>
    </div>
  )
}

export default App*/

import { Routes, Route, Navigate } from 'react-router-dom'
import Login from '@/pages/auth/Login'
import Register from '@/pages/auth/Register'
import Dashboard from '@/pages/Dashboard'
import MainLayout from '@/components/layout/MainLayout'
import ProtectedRoute from '@/routes/ProtectedRoute'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
      </Route>
    </Routes>
  )
}

