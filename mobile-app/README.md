# Accountancy Mobile App

A React Native mobile application for iOS and Android that connects to the Accountancy backend for Xero/QuickBooks accounting sync.

## Features

- **JWT Authentication** - Secure token-based login
- **Offline-First Architecture** - Queue transactions offline, sync when online
- **Real-time Sync Status** - See sync progress and pending items
- **Financial Dashboard** - View revenue, expenses, and net income
- **Device Security** - Device fingerprinting prevents token sharing
- **Push Notifications** - Get notified of sync events (framework ready)

## Technology Stack

- **Framework**: React Native 0.74
- **Build Tool**: Expo 51
- **Language**: TypeScript 5.2
- **State Management**: Zustand 4.4
- **HTTP Client**: Axios 1.6
- **Authentication**: JWT + Secure Storage

## Quick Start

### Prerequisites

- Node.js 18+
- npm 9+
- Expo CLI (`npm install -g expo-cli`)

### Installation

```bash
# Navigate to mobile app directory
cd mobile-app

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env.local

# Edit .env.local and set your API_BASE_URL
# For local development: http://YOUR_IP:8000/api/mobile
```

### Development

```bash
# Start development server
npm start

# Run on Android emulator
npm run android

# Run on iOS simulator (Mac only)
npm run ios

# Run on physical device
# Scan QR code from npm start output with Expo Go app
```

## Project Structure

```
mobile-app/
├── app.tsx                    # Main entry point
├── screens/                   # App screens
│   ├── LoginScreen.tsx        # Login form
│   └── HomeScreen.tsx         # Dashboard
├── services/
│   └── api.ts                 # API client (20+ endpoints)
├── stores/
│   └── appStore.ts            # Global state with Zustand
├── types/
│   └── index.ts               # TypeScript definitions
├── PHASE_2_SETUP.md           # Detailed setup guide
└── package.json               # Dependencies
```

## Documentation

- **PHASE_2_SETUP.md** - Complete setup guide with troubleshooting
- **In-code comments** - Every file is heavily documented
- **Type definitions** - Full TypeScript types in `types/index.ts`

## API Endpoints

The app connects to these backend endpoints:

### Authentication
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout

### User & Organization
- `GET /user/profile` - Get user profile
- `GET /org/summary` - Get financial summary

### Transactions
- `GET /transactions` - List transactions (paginated)
- `POST /transactions` - Create transaction

### Accounts
- `GET /accounts` - List accounts
- `GET /accounts/{id}` - Get account details

### Offline Sync
- `GET /sync-queue` - Get pending items
- `POST /sync-queue` - Add item to queue
- `POST /sync-queue/sync` - Sync pending items

### Push Notifications
- `POST /notifications/register-device` - Register for notifications
- `GET /notifications/history` - Get notification history

### Sync Status
- `GET /sync/status` - Get current sync status
- `GET /health` - Health check (no auth required)

## Environment Variables

Create `.env.local` based on `.env.example`:

```
API_BASE_URL=http://192.168.1.100:8000/api/mobile
ENVIRONMENT=development
DEBUG=true
API_TIMEOUT=30000
ENABLE_OFFLINE_SYNC=true
ENABLE_PUSH_NOTIFICATIONS=true
```

## Authentication Flow

1. User enters email/password on login screen
2. App sends request to backend
3. Backend returns access_token and refresh_token
4. Tokens stored in secure storage
5. Access token added to every API request header
6. When token expires, automatically refresh using refresh_token
7. If refresh fails, user returned to login screen

## Offline Sync Flow

1. User creates transaction while offline
2. Transaction added to local sync queue
3. Status shows "Offline mode"
4. When online, queue automatically syncs
5. Server returns confirmation
6. Transaction removed from queue
7. Status shows "All data synced"

## Common Issues

**Cannot connect to backend?**
- Check API_BASE_URL in .env.local matches your computer's IP
- Ensure backend is running on port 8000
- Device and computer must be on same WiFi

**App crashes on startup?**
- Check Metro bundler terminal for error messages
- Try: `npm start -- --clear` to clear cache
- Make sure all dependencies installed: `npm install`

**Login fails?**
- Backend accepts any email/password in demo mode
- Check backend logs for errors
- Verify network connection to backend

See PHASE_2_SETUP.md for detailed troubleshooting.

## Testing

```bash
# Type check
npm run type-check

# Lint code
npm run lint

# Run tests (set up in Phase 3)
npm test
```

## Building for Production

### Android
```bash
# Build APK for Google Play
npm run build-android
```

### iOS
```bash
# Build for App Store (Mac only)
npm run build-ios
```

Requires EAS (Expo Application Services) account.

## Next Steps (Phase 3)

Phase 3 will add:

- Tab navigation (Transactions, Accounts, Settings)
- Transaction list and create screens
- Account details screen
- Settings/preferences screen
- More complete offline sync handling
- Error recovery improvements
- Notification preferences UI

## Architecture Decisions

### Why Zustand?
- Simpler than Redux for this app size
- Easier to learn for new developers
- Minimal boilerplate
- Still powerful enough for complex state

### Why TypeScript?
- Catch errors at compile time
- Better IDE autocomplete
- Self-documenting code
- Matches backend type safety

### Why Axios?
- Better error handling than fetch
- Request/response interceptors
- Automatic retry logic
- Progress tracking for uploads

### Why Expo?
- One codebase for iOS + Android
- No build tools to set up
- Easy to test on physical devices
- Can eject to native if needed later

## Security Considerations

- ✅ Tokens stored in secure storage (not AsyncStorage)
- ✅ Device fingerprinting prevents token sharing
- ✅ Token refresh on expiry
- ✅ HTTPS in production (configure in app.json)
- ✅ Never hardcode API URLs or credentials
- ⚠️ Demo mode accepts any email/password (for testing only)

## Contributing

When adding new features:

1. Keep code well-documented with comments
2. Use TypeScript types (no `any`)
3. Follow existing code style
4. Test on both Android and iOS
5. Update PHASE_2_SETUP.md with new features

## License

MIT

## Support

Questions? Check:
1. PHASE_2_SETUP.md - Setup and troubleshooting
2. Code comments - Every file is documented
3. Type definitions - See types/index.ts
4. Backend docs - See MOBILE_API_SETUP.md in parent directory

---

**Built for Accountancy Mobile Platform**
*Phase 2: React Native Project Setup - November 2025*
