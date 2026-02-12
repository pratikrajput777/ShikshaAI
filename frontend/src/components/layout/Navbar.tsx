import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <div
      style={{
        padding: 12,
        borderBottom: '1px solid #ddd',
        display: 'flex',
        gap: 16,
      }}
    >
      <Link to="/dashboard">Dashboard</Link>
      <Link to="/profile">Profile</Link>
    </div>
  )
}
