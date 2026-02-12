import { Card } from '@/components/ui/Card'

export default function Dashboard() {
  return (
    <div style={{ padding: 24 }}>
      <h2>Dashboard</h2>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 16,
          marginTop: 20
        }}
      >
        <Card>Learning Module</Card>
        <Card>Assessment Module</Card>
        <Card>Interview Module</Card>
      </div>
    </div>
  )
}
