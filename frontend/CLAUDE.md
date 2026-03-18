# Frontend — Developer Guide

## Adding a New Page

1. Create component: `src/pages/NewPage.jsx`
2. Add route in `src/App.jsx`:
```jsx
import NewPage from './pages/NewPage'
// In routes array:
{ path: '/new-page', element: <NewPage /> }
```
3. Add entry in `src/modules/manifest.js`:
```js
// In the appropriate NAV_SECTIONS category:
{ label: 'New Page', path: '/new-page', icon: IconName }
```
4. Sidebar auto-generates from manifest — no manual sidebar edit needed

## manifest.js Structure
- `NAV_SECTIONS`: array of categories, each with `label`, `icon`, `items[]`
- Categories are collapsible in sidebar
- Each item: `{ label, path, icon }`
- Source of truth for all navigation

## Styling
- Tailwind CSS utility classes
- Icons: `lucide-react` (import from 'lucide-react')
- Dark theme with consistent color palette
- Mobile responsive (sidebar collapses)

## API Client
- File: `src/api/client.js`
- **CRITICAL**: URLs must be dynamic — use `window.location.origin`, NEVER hardcoded `localhost`
- WebSocket: dynamic protocol (`ws:`/`wss:` based on `location.protocol`)
- Axios instance with base URL from `window.location.origin`

## Build
- `npm run dev` — development with Vite HMR
- `npm run build` → `dist/` served statically by FastAPI in production
- PWA: manifest + service worker + workbox offline cache
