# Day 08: Frontend Foundation & Design System

## 🎯 Learning Objectives

By the end of this day, you will:
- Set up a modern React + TypeScript + Vite frontend project
- Create a comprehensive design system with design tokens
- Build reusable UI components following atomic design principles
- Implement API client with authentication interceptors
- Configure routing and protected routes
- Understand modern frontend architecture patterns

---

## 📚 What You'll Build

**Duration**: 8 hours  
**Difficulty**: Intermediate  
**Prerequisites**: JavaScript ES6+, React basics, TypeScript basics

### Deliverables
1. ✅ Complete Vite + React + TypeScript setup
2. ✅ Design system with tokens (colors, typography, spacing)
3. ✅ Base UI components (Button, Card, Input, Modal, etc.)
4. ✅ API client with Axios and interceptors
5. ✅ Auth context and protected routing
6. ✅ Layout components (responsive)

---

## 🏗️ Tech Stack (Frontend)

| Technology | Version | Purpose |
|-----------|---------|---------|
| **React** | 18.2+ | UI library |
| **TypeScript** | 5.0+ | Type safety |
| **Vite** | 5.0+ | Build tool (fast HMR) |
| **React Router** | 6.20+ | Client-side routing |
| **Axios** | 1.6+ | HTTP client |
| **TailwindCSS** | 3.4+ | Utility-first CSS (optional) |
| **Zustand** | 4.4+ | State management (lightweight) |

---

## 🎨 Design System Principles

### Design Tokens
Design tokens are the atomic values of your design system:

```typescript
// Color Palette
const colors = {
  primary: {
    50: '#eff6ff',
    500: '#3b82f6',  // Main brand color
    700: '#1d4ed8',
  },
  neutral: {
    0: '#ffffff',
    900: '#111827',
  },
  // ... more colors
}

// Typography Scale
const typography = {
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    // ... more sizes
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  }
}

// Spacing Scale (4px base)
const spacing = {
  1: '0.25rem',  // 4px
  2: '0.5rem',   // 8px
  4: '1rem',     // 16px
  8: '2rem',     // 32px
  // ... more spacing
}
```

### Component Variants
Each component should support multiple variants:

```typescript
// Button variants
<Button variant="primary">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>

// Button sizes
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>
```

---

## 🔧 Project Structure

```
frontend/
├── public/
│   ├── vite.svg
│   └── fonts/
├── src/
│   ├── assets/          # Images, icons
│   ├── components/
│   │   ├── ui/          # Base components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── index.ts
│   │   └── layout/      # Layout components
│   │       ├── Navbar.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   ├── contexts/        # React contexts
│   │   └── AuthContext.tsx
│   ├── hooks/           # Custom hooks
│   │   ├── useAuth.ts
│   │   └── useApi.ts
│   ├── lib/             # Utilities
│   │   ├── api.ts       # Axios client
│   │   └── auth.ts      # Auth helpers
│   ├── pages/           # Page components
│   │   ├── auth/
│   │   │   ├── Login.tsx
│   │   │   └── Register.tsx
│   │   └── Dashboard.tsx
│   ├── routes/          # Routing config
│   │   └── index.tsx
│   ├── styles/          # Global styles
│   │   ├── theme.ts     # Design tokens
│   │   └── global.css   # Global CSS
│   ├── types/           # TypeScript types
│   │   └── index.ts
│   ├── App.tsx          # Root component
│   ├── main.tsx         # Entry point
│   └── vite-env.d.ts
├── .env.local           # Environment variables
├── .gitignore
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## 🧩 Key Concepts

### 1. Atomic Design
Organize components by complexity:
- **Atoms**: Button, Input, Icon (basic building blocks)
- **Molecules**: SearchBar, FormField (simple combinations)
- **Organisms**: Navbar, Card with actions (complex components)
- **Templates**: Page layouts
- **Pages**: Full pages with data

### 2. Design Tokens
Centralize all design decisions (colors, spacing, typography) in one place. Benefits:
- Consistency across app
- Easy theming (light/dark mode)
- Quick redesigns (change tokens, not components)

### 3. Component Composition
Build complex UIs from simple components:
```tsx
<Card>
  <Card.Header>
    <Card.Title>Welcome</Card.Title>
  </Card.Header>
  <Card.Body>
    <p>Content here</p>
  </Card.Body>
  <Card.Footer>
    <Button>Action</Button>
  </Card.Footer>
</Card>
```

### 4. API Client Pattern
Centralize HTTP requests:
```typescript
// lib/api.ts
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

// Request interceptor (add auth token)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor (handle errors globally)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

### 5. Protected Routes
Require authentication for specific routes:
```tsx
<Route element={<ProtectedRoute />}>
  <Route path="/dashboard" element={<Dashboard />} />
  <Route path="/profile" element={<Profile />} />
</Route>
```

---

## 🎓 Learning Resources

### Official Documentation
- [React Docs](https://react.dev) - React 18+ with Hooks
- [TypeScript Handbook](https://www.typescriptlang.org/docs/) - TS fundamentals
- [Vite Guide](https://vitejs.dev/guide/) - Vite concepts
- [React Router](https://reactrouter.com/en/main) - Routing guide

### Design Systems
- [Material Design](https://m3.material.io/) - Google's design system
- [Ant Design](https://ant.design/) - Enterprise design system
- [Chakra UI](https://chakra-ui.com/) - Component library
- [TailwindCSS](https://tailwindcss.com/) - Utility classes

### Best Practices
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Bulletproof React](https://github.com/alan2207/bulletproof-react) - Architecture guide
- [Frontend Checklist](https://frontendchecklist.io/) - Quality checklist

---

## ⏱️ Time Estimates

| Phase | Duration | Complexity |
|-------|----------|------------|
| Setup & Configuration | 2h | Easy |
| Design System | 4h | Medium |
| API & Auth Setup | 2h | Medium |
| **Total** | **8h** | **Medium** |

---

## ✅ Success Criteria

By the end of Day 08, you should have:
- [x] Vite project running (`npm run dev`)
- [x] TypeScript strict mode enabled with no errors
- [x] Design system with at least 5 base components
- [x] API client successfully calling backend
- [x] Protected routes redirecting unauthenticated users
- [x] Responsive layout (mobile, tablet, desktop)
- [x] Dark mode toggle working (bonus)

---

## 🚀 Getting Started

1. **Read this README** to understand objectives
2. **Follow tasks.md** for step-by-step implementation
3. **Use ai-prompts.md** when you need AI assistance
4. **Refer to troubleshoot.md** if you encounter errors
5. **Run tests from test.md** to validate your work

---

## 💡 Pro Tips

- **Start simple**: Build basic components before adding complexity
- **Think reusability**: Every component should be reusable with props
- **Type everything**: Use TypeScript for better DX and fewer bugs
- **Consistent naming**: Follow naming conventions (PascalCase for components)
- **Mobile-first**: Design for mobile, then scale up to desktop
- **Accessibility**: Use semantic HTML, ARIA labels, keyboard navigation

---

**Next**: [Day 09 - Core Pages & Authentication](../day-09/readme.md)  
**Previous**: [Day 07 - WebSockets & Completion](../day-07/readme.md)

---

*Happy Coding! 🎨*
