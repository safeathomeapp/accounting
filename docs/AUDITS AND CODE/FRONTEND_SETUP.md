# Frontend Setup & Architecture

## Overview

Modern React-based web frontend for the Accountancy platform. Designed to be responsive and work on both desktop and mobile browsers.

## Technology Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18.2.0 | UI library |
| Vite | 5.0.0 | Build tool & dev server |
| TailwindCSS | 3.3.0 | Responsive styling |
| Zustand | 4.4.0 | State management |
| Axios | 1.6.0 | HTTP client |

## Quick Start

### Development

```bash
cd C:/Users/kevth/desktop/projects/accountancy/frontend
npm install        # Install dependencies (already done)
npm run dev        # Start dev server on http://localhost:3000
```

### Production Build

```bash
npm run build      # Creates optimized build in dist/
npm run preview    # Preview production build locally
```

## Architecture

### Directory Structure

```
src/
├── pages/              # Page components
│   ├── Login.jsx      # Login form page
│   └── Dashboard.jsx  # Main dashboard
├── components/         # Reusable components (add as needed)
├── stores/            # Zustand state stores
│   └── authStore.js   # Authentication state
├── services/          # API clients
│   └── api.js         # Axios API client
├── hooks/             # Custom React hooks
├── App.jsx            # Root app component
├── main.jsx           # React DOM entry point
└── index.css          # Global styles (TailwindCSS)
```

### Data Flow

```
User Browser
    ↓
Frontend (React + Vite)
    ↓
API Service (Axios)
    ↓
Backend (FastAPI)
    ↓
Database
```

### Authentication Flow

1. User enters credentials on Login page
2. `authStore.login()` makes POST to `/api/v1/auth/login`
3. Backend returns JWT token
4. Token stored in `localStorage`
5. Token added to all subsequent API requests
6. User redirected to Dashboard

## Components

### Login Page (`src/pages/Login.jsx`)

**Purpose:** Authenticate user and obtain JWT token

**Features:**
- Email/password form
- Error display
- Loading state
- Pre-filled demo credentials

**API Endpoint:** `POST /api/v1/auth/login`

**Response:**
```json
{
  "token": "eyJhbGc...",
  "user": {
    "email": "test@example.com",
    "name": "Test User",
    "id": "1"
  }
}
```

### Dashboard (`src/pages/Dashboard.jsx`)

**Purpose:** Display financial summary and system status

**Features:**
- Stats cards (accounts, transactions, revenue, sync status)
- Responsive grid layout
- Last sync timestamp
- Logout button
- Mock data fallback

**API Endpoint:** `GET /api/v1/dashboard/summary`

**Expected Response:**
```json
{
  "totalAccounts": 3,
  "totalTransactions": 1247,
  "lastSync": "2025-11-27T18:30:00Z",
  "syncStatus": "Success",
  "revenue": "$125,430.00",
  "expenses": "$45,230.00"
}
```

## State Management

### Auth Store (`src/stores/authStore.js`)

Using Zustand for lightweight state management.

**State:**
- `isAuthenticated` - User logged in
- `user` - Current user object
- `loading` - Login request in progress
- `error` - Error message

**Actions:**
- `login(email, password)` - Authenticate user
- `logout()` - Clear auth and redirect
- `checkAuth()` - Check localStorage for existing token

**Usage:**
```jsx
const { isAuthenticated, user, login, logout } = useAuthStore()
```

## API Client (`src/services/api.js`)

Axios-based HTTP client with automatic token injection.

**Features:**
- Base URL configuration via `VITE_API_BASE_URL`
- Automatic Bearer token injection
- Request/response interceptors

**Usage:**
```jsx
import { authAPI, dashboardAPI } from '@/services/api'

// Login
const response = await authAPI.login(email, password)

// Dashboard data
const summary = await dashboardAPI.getSummary()
```

## Environment Variables

Create `.env.local` (git-ignored):

```
VITE_API_BASE_URL=http://192.168.1.143:8000/api/v1
```

Default fallback: `http://192.168.1.143:8000/api/v1`

## Styling with TailwindCSS

### Classes Used

- `flex`, `grid` - Layout
- `bg-white`, `bg-gray-100` - Colors
- `rounded-lg`, `shadow` - Styling
- `hover:bg-blue-700` - Interactive states
- `md:grid-cols-2`, `lg:grid-cols-4` - Responsive design

### Adding New Styles

Edit `src/index.css` for global styles.

Use TailwindCSS utility classes directly in JSX (no additional CSS needed).

Example responsive grid:
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  {/* Cards */}
</div>
```

## Common Tasks

### Add a New Page

1. Create `src/pages/NewPage.jsx`
2. Import in `src/App.jsx`
3. Add routing logic

### Add a New Component

1. Create `src/components/ComponentName.jsx`
2. Import where needed
3. Use as JSX component

### Add API Endpoint

1. Add method in `src/services/api.js`
2. Import in component
3. Call with `await`

### Debug API Calls

Check browser DevTools Network tab:
- Request URL: Should match backend endpoint
- Headers: Should include `Authorization: Bearer <token>`
- Response: Check status code and JSON

## Troubleshooting

### Login Fails: "Not Found"
**Cause:** Backend not restarted after adding auth routes
**Fix:** Restart backend with `python -m uvicorn backend.main:app --reload ...`

### "Invalid Token"
**Cause:** Token expired or localStorage corrupted
**Fix:** Clear browser cookies/storage and log in again

### CORS Error
**Cause:** Backend CORS not configured
**Fix:** Check `backend/main.py` has CORS middleware configured

### Vite Not Opening in Browser
**Fix:** Manually open `http://localhost:3000`

---

See `docs/SESSION_NOTES/MONTH6_PHASE3.md` for current session status.
