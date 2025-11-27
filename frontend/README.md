# Accountancy Frontend

Modern React + Vite web frontend for the Accountancy platform. Responsive design works on desktop and mobile browsers.

## Quick Start

```bash
# Install dependencies (one time)
npm install

# Start development server
npm run dev

# Open http://localhost:3000 in browser
```

## Development

### Login Credentials
- **Email:** test@example.com
- **Password:** (anything)

### File Structure
```
src/
├── pages/            # Page components
├── stores/           # State management (Zustand)
├── services/         # API client
├── App.jsx          # Root component
└── main.jsx         # Entry point
```

### Available Scripts

```bash
npm run dev       # Start dev server
npm run build     # Production build
npm run preview   # Preview production build
npm run lint      # Run ESLint
```

## Backend Integration

**API Base URL:** `http://192.168.1.143:8000/api/v1`

### Required Backend Endpoints

- `POST /auth/login` - Authenticate user, return JWT
- `GET /dashboard/summary` - Get financial summary

### Backend Status

Currently running on `http://192.168.1.143:8000`

**Note:** Backend needs to be restarted if auth endpoints aren't responding.

## Technology

- **React** 18.2 - UI framework
- **Vite** 5.0 - Fast build tool
- **TailwindCSS** 3.3 - Responsive styling
- **Zustand** 4.4 - State management
- **Axios** 1.6 - HTTP client

## Next Steps

1. Restart backend (new auth routes added)
2. Test login flow
3. Connect dashboard to real API data
4. Add more pages (transactions, accounts, etc.)

## Documentation

See `/docs/FRONTEND_SETUP.md` for detailed architecture and API integration guide.

See `/docs/SESSION_NOTES/MONTH6_PHASE3.md` for current session status.

## Troubleshooting

**Login fails with "Not Found"?**
→ Backend needs restart to load new auth routes

**CORS error?**
→ Backend CORS middleware should be configured

**Can't connect to backend?**
→ Check backend is running on `http://192.168.1.143:8000`

---

Built with React + Vite + TailwindCSS • November 2025
