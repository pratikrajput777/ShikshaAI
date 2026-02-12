import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import Sidebar from './Sidebar'

export default function MainLayout() {
  return (
    <div>
      <Navbar />

      <div style={{ display: 'flex' }}>
        <Sidebar />

        <main style={{ padding: 24, flex: 1 }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}






/*import { Outlet, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

export default function MainLayout() {
  const { logout } = useAuth()

  return (
    <div>
      <header
        style={{
          padding: 16,
          borderBottom: '1px solid #ddd',
          display: 'flex',
          gap: 12,
        }}
      >
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/learning">Learning</Link>
        <Link to="/assessment">Assessment</Link>
        <Link to="/interview">Interview</Link>

        <button onClick={logout} style={{ marginLeft: 'auto' }}>
          Logout
        </button>
      </header>

      <main style={{ padding: 24 }}>
        <Outlet />
      </main>
    </div>
  )
}*/
