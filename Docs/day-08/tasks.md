# Day 08: Frontend Foundation - Implementation Tasks

## ⏱️ Estimated Time: 8 hours

---

## Phase 1: Setup & Configuration (2 hours)

### Task 1.1: Initialize Vite + React + TypeScript Project
**Time**: 30 minutes

```bash
cd /home/tushka/Projects/shikshaAI

# Create frontend directory
npm create vite@latest frontend -- --template react-ts

cd frontend

# Install dependencies
npm install
```

**Verification**:
- `npm run dev` starts development server
- App loads at http://localhost:5173
- No TypeScript errors

---

### Task 1.2: Install Core Dependencies
**Time**: 20 minutes

```bash
# Routing
npm install react-router-dom

# HTTP client
npm install axios

# State management (choose one)
npm install zustand
# OR
npm install @reduxjs/toolkit react-redux

# UI framework (choose one or build custom)
npm install @mui/material @mui/icons-material @emotion/react @emotion/styled
# OR
npm install tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Development dependencies
npm install -D @types/node
```

**Configuration**:

Create `vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

Update `tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Verification**:
- All packages installed successfully
- TypeScript strict mode enabled
- Aliases working (`@/` imports resolve)

---

### Task 1.3: Create Project Structure
**Time**: 20 minutes

```bash
cd frontend/src

# Create directory structure
mkdir -p components/{ui,layout}
mkdir -p contexts
mkdir -p hooks
mkdir -p lib
mkdir -p pages/{auth,learning,assessment,interview,gamification,subscription}
mkdir -p routes
mkdir -p styles
mkdir -p types
mkdir -p assets/{images,icons}
```

**Verification**:
- All directories created
- Structure matches planning docs

---

### Task 1.4: Setup Environment Variables
**Time**: 10 minutes

Create `frontend/.env.local`:
```env
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
VITE_STRIPE_PUBLIC_KEY=pk_test_your_key_here
VITE_GOOGLE_CLIENT_ID=your_google_client_id
```

Create `frontend/.env.example`:
```env
VITE_API_URL=
VITE_WS_URL=
VITE_STRIPE_PUBLIC_KEY=
VITE_GOOGLE_CLIENT_ID=
```

Create `frontend/src/config.ts`:
```typescript
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  stripePublicKey: import.meta.env.VITE_STRIPE_PUBLIC_KEY || '',
  googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
}
```

**Verification**:
- Environment variables accessible via `import.meta.env`
- Config object properly typed

---

### Task 1.5: Create TypeScript Types
**Time**: 20 minutes

Create `frontend/src/types/index.ts`:
```typescript
// User types
export interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  profile_picture?: string
  is_premium: boolean
  subscription_tier: 'free' | 'basic' | 'pro' | 'enterprise'
  created_at: string
}

// Auth types
export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  username: string
  first_name: string
  last_name: string
}

export interface AuthTokens {
  access: string
  refresh: string
}

export interface AuthResponse {
  user: User
  tokens: AuthTokens
}

// API response types
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// Component prop types
export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
  loading?: boolean
  disabled?: boolean
  onClick?: () => void
  children: React.ReactNode
}

export interface CardProps {
  children: React.ReactNode
  className?: string
  hoverable?: boolean
}

export interface ModalProps {
  open: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
}
```

**Verification**:
- Types compile without errors
- All core types defined

---

## Phase 2: Design System (4 hours)

### Task 2.1: Create Design Tokens
**Time**: 45 minutes

Create `frontend/src/styles/theme.ts`:
```typescript
export const theme = {
  colors: {
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',  // Main brand
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },
    secondary: {
      50: '#f0fdf4',
      100: '#dcfce7',
      500: '#22c55e',
      700: '#15803d',
      900: '#14532d',
    },
    accent: {
      50: '#fdf4ff',
      500: '#d946ef',
      700: '#a21caf',
    },
    neutral: {
      0: '#ffffff',
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
      950: '#030712',
    },
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',
  },
  
  typography: {
    fontFamily: {
      sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      mono: '"Fira Code", "Courier New", monospace',
    },
    fontSize: {
      xs: '0.75rem',    // 12px
      sm: '0.875rem',   // 14px
      base: '1rem',     // 16px
      lg: '1.125rem',   // 18px
      xl: '1.25rem',    // 20px
      '2xl': '1.5rem',  // 24px
      '3xl': '1.875rem',// 30px
      '4xl': '2.25rem', // 36px
      '5xl': '3rem',    // 48px
    },
    fontWeight: {
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
      extrabold: '800',
    },
    lineHeight: {
      tight: '1.25',
      normal: '1.5',
      relaxed: '1.75',
    },
  },
  
  spacing: {
    0: '0',
    1: '0.25rem',   // 4px
    2: '0.5rem',    // 8px
    3: '0.75rem',   // 12px
    4: '1rem',      // 16px
    5: '1.25rem',   // 20px
    6: '1.5rem',    // 24px
    8: '2rem',      // 32px
    10: '2.5rem',   // 40px
    12: '3rem',     // 48px
    16: '4rem',     // 64px
    20: '5rem',     // 80px
  },
  
  borderRadius: {
    none: '0',
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    full: '9999px',
  },
  
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1)',
  },
  
  transitions: {
    fast: '150ms ease-in-out',
    normal: '250ms ease-in-out',
    slow: '350ms ease-in-out',
  },
  
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
}

export type Theme = typeof theme
```

**Verification**:
- Theme object properly typed
- All tokens accessible

---

### Task 2.2: Create Global Styles
**Time**: 30 minutes

Create `frontend/src/styles/global.css`:
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

:root {
  /* Colors */
  --color-primary: #3b82f6;
  --color-primary-dark: #1d4ed8;
  --color-secondary: #22c55e;
  --color-accent: #d946ef;
  
  /* Backgrounds */
  --bg-primary: #ffffff;
  --bg-secondary: #f9fafb;
  --bg-tertiary: #f3f4f6;
  
  /* Text */
  --text-primary: #111827;
  --text-secondary: #6b7280;
  --text-tertiary: #9ca3af;
  
  /* Borders */
  --border-color: #e5e7eb;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}

[data-theme='dark'] {
  --bg-primary: #111827;
  --bg-secondary: #1f2937;
  --bg-tertiary: #374151;
  --text-primary: #f9fafb;
  --text-secondary: #d1d5db;
  --text-tertiary: #9ca3af;
  --border-color: #374151;
}

html, body, #root {
  height: 100%;
  width: 100%;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 16px;
  line-height: 1.5;
  color: var(--text-primary);
  background-color: var(--bg-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Utility classes */
.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1rem;
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.text-gradient {
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

.animate-slide-in {
  animation: slideInRight 0.3s ease-in-out;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* Scrollbar styles */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}
```

Update `frontend/src/main.tsx`:
```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './styles/global.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

**Verification**:
- Google Fonts loading
- CSS variables working
- Dark mode toggle ready

---

### Task 2.3: Build Button Component
**Time**: 45 minutes

Create `frontend/src/components/ui/Button.tsx`:
```typescript
import React from 'react'
import './Button.css'

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
  loading?: boolean
  disabled?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void
  type?: 'button' | 'submit' | 'reset'
  children: React.ReactNode
  className?: string
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  disabled = false,
  leftIcon,
  rightIcon,
  onClick,
  type = 'button',
  children,
  className = '',
}) => {
  const classes = [
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    fullWidth && 'btn-full-width',
    loading && 'btn-loading',
    disabled && 'btn-disabled',
    className,
  ].filter(Boolean).join(' ')

  return (
    <button
      type={type}
      className={classes}
      onClick={onClick}
      disabled={disabled || loading}
    >
      {loading && <span className="btn-spinner" />}
      {!loading && leftIcon && <span className="btn-icon-left">{leftIcon}</span>}
      <span className="btn-content">{children}</span>
      {!loading && rightIcon && <span className="btn-icon-right">{rightIcon}</span>}
    </button>
  )
}
```

Create `frontend/src/components/ui/Button.css`:
```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 500;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 150ms ease-in-out;
  font-family: inherit;
  position: relative;
}

.btn:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Sizes */
.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.btn-md {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
}

.btn-lg {
  padding: 1rem 2rem;
  font-size: 1.125rem;
}

/* Variants */
.btn-primary {
  background-color: var(--color-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-secondary {
  background-color: var(--color-secondary);
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  filter: brightness(0.9);
}

.btn-outline {
  background-color: transparent;
  border: 2px solid var(--color-primary);
  color: var(--color-primary);
}

.btn-outline:hover:not(:disabled) {
  background-color: var(--color-primary);
  color: white;
}

.btn-ghost {
  background-color: transparent;
  color: var(--text-primary);
}

.btn-ghost:hover:not(:disabled) {
  background-color: var(--bg-tertiary);
}

.btn-danger {
  background-color: var(--color-error);
  color: white;
}

/* States */
.btn-full-width {
  width: 100%;
}

.btn-disabled,
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-loading {
  pointer-events: none;
}

.btn-spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
```

**Verification**:
```tsx
// Test in App.tsx
<Button variant="primary">Primary</Button>
<Button variant="secondary" size="sm">Small</Button>
<Button variant="outline" loading>Loading...</Button>
```

---

### Task 2.4: Build Card Component
**Time**: 30 minutes

Create `frontend/src/components/ui/Card.tsx`:
```typescript
import React from 'react'
import './Card.css'

export interface CardProps {
  children: React.ReactNode
  className?: string
  hoverable?: boolean
  onClick?: () => void
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  hoverable = false,
  onClick,
}) => {
  const classes = [
    'card',
    hoverable && 'card-hoverable',
    onClick && 'card-clickable',
    className,
  ].filter(Boolean).join(' ')

  return (
    <div className={classes} onClick={onClick}>
      {children}
    </div>
  )
}

// Sub-components
interface CardHeaderProps {
  children: React.ReactNode
  className?: string
}

export const CardHeader: React.FC<CardHeaderProps> = ({ children, className = '' }) => (
  <div className={`card-header ${className}`}>{children}</div>
)

export const CardBody: React.FC<CardHeaderProps> = ({ children, className = '' }) => (
  <div className={`card-body ${className}`}>{children}</div>
)

export const CardFooter: React.FC<CardHeaderProps> = ({ children, className = '' }) => (
  <div className={`card-footer ${className}`}>{children}</div>
)

// Compound component pattern
Card.Header = CardHeader
Card.Body = CardBody
Card.Footer = CardFooter
```

Create `frontend/src/components/ui/Card.css`:
```css
.card {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: all 250ms ease-in-out;
}

.card-hoverable:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.card-clickable {
  cursor: pointer;
}

.card-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.card-body {
  padding: 1.5rem;
}

.card-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
}
```

**Verification**:
```tsx
<Card hoverable>
  <Card.Header>Card Title</Card.Header>
  <Card.Body>Card content here</Card.Body>
  <Card.Footer>Footer actions</Card.Footer>
</Card>
```

---

### Task 2.5: Build Input Component
**Time**: 30 minutes

Create `frontend/src/components/ui/Input.tsx`:
```typescript
import React from 'react'
import './Input.css'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  fullWidth?: boolean
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      fullWidth = false,
      className = '',
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).slice(2, 9)}`
    
    return (
      <div className={`input-wrapper ${fullWidth ? 'input-full-width' : ''}`}>
        {label && (
          <label htmlFor={inputId} className="input-label">
            {label}
          </label>
        )}
        <div className="input-container">
          {leftIcon && <span className="input-icon-left">{leftIcon}</span>}
          <input
            ref={ref}
            id={inputId}
            className={`input ${error ? 'input-error' : ''} ${className}`}
            {...props}
          />
          {rightIcon && <span className="input-icon-right">{rightIcon}</span>}
        </div>
        {error && <span className="input-error-text">{error}</span>}
        {helperText && !error && <span className="input-helper-text">{helperText}</span>}
      </div>
    )
  }
)

Input.displayName = 'Input'
```

Create `frontend/src/components/ui/Input.css`:
```css
.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.input-full-width {
  width: 100%;
}

.input-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.input {
  width: 100%;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  font-family: inherit;
  color: var(--text-primary);
  background-color: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  transition: all 150ms ease-in-out;
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-error {
  border-color: var(--color-error);
}

.input-error:focus {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.input-icon-left,
.input-icon-right {
  position: absolute;
  display: flex;
  align-items: center;
  color: var(--text-tertiary);
}

.input-icon-left {
  left: 1rem;
}

.input-icon-right {
  right: 1rem;
}

.input:has(~ .input-icon-left) {
  padding-left: 3rem;
}

.input:has(~ .input-icon-right) {
  padding-right: 3rem;
}

.input-error-text {
  font-size: 0.875rem;
  color: var(--color-error);
}

.input-helper-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
}
```

**Verification**: Test with error states, icons, labels

---

**(Continue with remaining tasks...)**

### Task 2.6: Build Modal Component  
### Task 2.7: Build Badge Component  
### Task 2.8: Build Spinner Component  

---

## Phase 3: API & Auth Setup (2 hours)

### Task 3.1: Create API Client
### Task 3.2: Setup Authentication Context
### Task 3.3: Create Protected Route Component
### Task 3.4: Implement Auth Hooks

---

## ✅ Completion Checklist

- [ ] Vite project initialized and running
- [ ] All dependencies installed
- [ ] TypeScript configured with strict mode
- [ ] Project structure created
- [ ] Design tokens defined (theme.ts)
- [ ] Global styles implemented
- [ ] Button component complete
- [ ] Card component complete
- [ ] Input component complete
- [ ] Modal component complete
- [ ] Badge component complete
- [ ] Spinner component complete
- [ ] API client configured
- [ ] Auth context implemented
- [ ] Protected routes working
- [ ] Dark mode toggle functional

---

**Next**: [Day 09 - Core Pages & Authentication](../day-09/tasks.md)
