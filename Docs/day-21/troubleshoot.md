# Day 21: Mobile Gamification & Polish - Troubleshooting Guide

## 🔧 Common Issues and Solutions

This guide covers common problems you might encounter during Day 21.

---

## Setup Issues

### Issue 1: Dependencies Not Installing

**Problem**: Package installation fails

**Solution**:
```bash
# Clear cache
npm cache clean --force  # For frontend
# OR
pip cache purge  # For backend

# Reinstall
rm -rf node_modules package-lock.json
npm install
# OR
pip install -r requirements.txt --force-reinstall
```

### Issue 2: Environment Variables Not Loading

**Problem**: Config values are undefined

**Solution**:
1. Check `.env.local` file exists
2. Verify variable names match exactly
3. Restart dev server after changes
4. Use `import.meta.env` (not `process.env`) in Vite

```typescript
// Correct
const apiUrl = import.meta.env.VITE_API_URL

// Wrong  
const apiUrl = process.env.VITE_API_URL
```

---

## Implementation Issues

### Issue 3: Component Not Rendering

**Problem**: Component shows blank or crashes

**Symptoms**:
- Blank screen
- Console error: "Cannot read property of undefined"

**Solutions**:

1. **Check imports**:
```typescript
// Correct
import { Button } from '@/components/ui/Button'

// Wrong
import Button from '@/components/ui/Button'  // If using named export
```

2. **Verify props**:
```typescript
// Add default props
const MyComponent: React.FC<Props> = ({ 
  data = [],  // Default value
  onSubmit 
}) => {
  // ...
}
```

3. **Check hooks usage**:
```typescript
// Hooks must be at top level
// ❌ Wrong
if (condition) {
  const [state, setState] = useState()
}

// ✅ Correct
const [state, setState] = useState()
if (condition) {
  setState(value)
}
```

### Issue 4: TypeScript Errors

**Problem**: Type errors blocking compilation

**Solutions**:

```typescript
// Use proper types
interface User {
  id: number
  name: string
}

// Not 'any'
const users: User[] = []  // ✅
const users: any = []     // ❌

// Use type guards
if (typeof value === 'string') {
  // TypeScript knows value is string here
  console.log(value.toLowerCase())
}

// Use optional chaining
const email = user?.profile?.email
```

---

## Performance Issues

### Issue 8: Slow Page Load

**Problem**: Pages loading slowly

**Solutions**:

1. **Check Network tab**: Identify slow requests
2. **Implement code splitting**:
```typescript
// Lazy load routes
const Dashboard = lazy(() => import('./pages/Dashboard'))
```

3. **Add loading states**:
```typescript
const { data, isLoading } = useQuery('key', fetchFn)

if (isLoading) return <Spinner />
```

4. **Optimize images**: Convert to WebP, add lazy loading

### Issue 9: Memory Leaks

**Problem**: App gets slower over time

**Solutions**:

```typescript
// Clean up effects
useEffect(() => {
  const subscription = api.subscribe()
  
  return () => {
    subscription.unsubscribe()  // Cleanup
  }
}, [])

// Clean up timers
useEffect(() => {
  const timer = setInterval(() => {}, 1000)
  
  return () => clearInterval(timer)
}, [])
```

---

## Testing Issues

### Issue 10: Tests Passing Locally But Failing in CI

**Problem**: CI tests fail but local tests pass

**Solutions**:

1. **Check for timing issues**:
```typescript
// Use waitFor  
await waitFor(() => {
  expect(screen.getByText('Success')).toBeInTheDocument()
})
```

2. **Ensure clean state**:
```typescript
beforeEach(() => {
  // Reset everything
  cleanup()
  localStorage.clear()
})
```

3. **Fix timezone issues**:
```python
# Use timezone-aware datetimes
from django.utils import timezone
now = timezone.now()  # Not datetime.now()
```

---

## Build / Deployment Issues

### Issue 11: Build Fails

**Problem**: Production build errors

**Solutions**:

```bash
# Check for TypeScript errors
npm run type-check

# Check bundle size
npm run build -- --analyze

# Clear cache and rebuild
rm -rf dist node_modules/.vite
npm run build
```

### Issue 12: Environment-Specific Issues

**Problem**: Works in dev but not production

**Solutions**:

1. Check environment variables are set in production
2. Verify CORS settings for production domain
3. Check console for errors (different API URLs?)
4. Ensure production builds don't have dev-only code

---

## 🆘 Still Stuck?

If these solutions don't help:

1. **Check error logs**: Full error message often has the answer
2. **Search the error**: Google the exact error message
3. **Use AI prompts**: See `ai-prompts.md` for debugging prompts
4. **Check Day 20**: Ensure previous day completed correctly
5. **Review test.md**: Run all validation tests
6. **Git diff**: What changed since it last worked?

---

## 📞 Getting Help

- **Stack Overflow**: Tag with specific tech (react, django, etc.)
- **GitHub Issues**: Check if others hit same problem
- **Documentation**: Official docs are always up-to-date
- **Community**: Join Discord/Slack for real-time help

---

**Most common fix**: Restart the dev server! 🔄

Many issues resolve with a simple restart.
