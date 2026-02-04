import React from 'react'
import './Card.css'

interface CardProps {
  children: React.ReactNode
  className?: string
}

export const Card: React.FC<CardProps> = ({ children, className = '' }) => {
  return <div className={`card ${className}`}>{children}</div>
}

<Card>
  <h3>ShikshaAI Card</h3>
  <p>Backend already ready ✔</p>
</Card>

