import { Link } from 'react-router-dom'

export default function Sidebar() {
  return (
    <div
      style={{
        width: 200,
        borderRight: '1px solid #ddd',
        padding: 16,
      }}
    >
      <p><Link to="/dashboard">Dashboard</Link></p>
      <p><Link to="/profile">Profile</Link></p>
      <p><Link to="/learning">Learning</Link></p>
      <p><Link to="/assessment">Assessment</Link></p>
      <p><Link to="/interview">Interview</Link></p>
    </div>
  )
}
