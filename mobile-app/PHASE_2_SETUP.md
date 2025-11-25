# Phase 2: React Native Project Setup - Step-by-Step Guide

## Overview

In Phase 2, we've created a complete React Native project structure with:

- **Package.json**: Dependencies and npm scripts
- **Expo configuration**: app.json for iOS/Android settings
- **TypeScript setup**: Full type safety for your app
- **API Client**: Ready-to-use service for backend communication
- **State Management**: Zustand store for global state
- **Two screens**: LoginScreen and HomeScreen
- **Heavy documentation**: Every file is explained

This guide walks you through setting up this project on your computer.

---

## Prerequisites

Before starting, ensure you have:

1. **Node.js 18+** - Download from https://nodejs.org/
   - Verify: Run `node --version` in terminal
   - Should output: `v18.x.x` or higher

2. **npm 9+** - Usually installed with Node.js
   - Verify: Run `npm --version` in terminal
   - Should output: `9.x.x` or higher

3. **Expo CLI** - Install globally
   ```bash
   npm install -g expo-cli
   ```
   - Verify: Run `expo --version` in terminal

4. **Git** - For version control
   - Already installed if you're reading this!

---

## Step 1: Navigate to the Mobile App Directory

Open your terminal/command prompt and navigate to the mobile app folder:

```bash
# On Windows (adjust path to your setup)
cd C:\Users\kevth\desktop\projects\accountancy\mobile-app

# On Mac/Linux
cd /path/to/accountancy/mobile-app
```

Verify you see these files:
```
app.json
babel.config.js
package.json
tsconfig.json
.env.example
```

---

## Step 2: Install Dependencies

Install all required npm packages:

```bash
npm install
```

This command:
- Downloads ~800+ MB of packages
- Takes 2-5 minutes
- Creates a `node_modules` folder (this is normal and large)

**Wait for it to complete.** You should see:
```
added 1234 packages in 2m45s
```

---

## Step 3: Create Environment Configuration

Copy the environment example file and create your actual env file:

```bash
# Copy the example file
cp .env.example .env.local

# On Windows
copy .env.example .env.local
```

Now edit `.env.local` and update the API URL:

**For local development** (testing with backend on your computer):
```
API_BASE_URL=http://192.168.1.100:8000/api/mobile
```

Replace `192.168.1.100` with your computer's IP address:
- **Windows**: Open Command Prompt, run `ipconfig`, look for "IPv4 Address"
- **Mac**: System Preferences → Network → Wi-Fi → Advanced → IP address
- **Linux**: Run `hostname -I`

**For production** (testing with backend on a server):
```
API_BASE_URL=https://api.yourdomain.com/api/mobile
```

---

## Step 4: Verify the Project Structure

The project should look like this:

```
mobile-app/
├── app.tsx                 # Main entry point
├── app.json               # Expo configuration
├── package.json           # Dependencies
├── tsconfig.json          # TypeScript config
├── babel.config.js        # Babel compiler config
├── .env.example           # Environment variables template
├── .env.local             # Your actual environment variables (CREATED)
│
├── screens/               # App screens
│   ├── LoginScreen.tsx    # Login form
│   ├── HomeScreen.tsx     # Dashboard after login
│   └── (more in Phase 3)
│
├── services/              # API communication
│   └── api.ts             # API client (600+ lines)
│
├── stores/                # Global state management
│   └── appStore.ts        # Zustand store
│
├── types/                 # TypeScript types
│   └── index.ts           # All data types
│
└── node_modules/          # Dependencies (large, ignore)
```

---

## Step 5: Start the Development Server

Now start the Expo development server:

```bash
npm start
```

You should see output like:

```
Starting metro bundler...
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
│ Metro waiting on port 19000
│ Exporting: 96%
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

› Metro waiting on port 19000...
› Expo waiting on port 19001...

Expo Go URL: exp://192.168.1.100:19000
Android emulator URL: exp://192.168.1.100:19000
...
```

**Keep this terminal open!** This is the development server.

---

## Step 6: Run on Android Emulator

In a new terminal window, run:

```bash
npm run android
```

First time setup:
1. Android Studio must be installed
2. AVD (Android Virtual Device) must exist
3. Emulator will boot (takes 1-2 minutes)
4. App will install and run

Expected output:
```
Building APK...
Installing APK on emulator...
Starting app...
```

Then you'll see the login screen on the emulator!

---

## Step 7: Run on iOS (Mac Only)

If you have a Mac:

```bash
npm run ios
```

You must have:
- Xcode installed
- iOS Simulator available

---

## Step 8: Run on Your Physical Device

### Android Device:
1. Install Expo Go app from Google Play Store
2. Ensure phone is on same WiFi as computer
3. Scan QR code from `npm start` output with Expo Go app
4. App opens on your phone!

### iPhone:
1. Install Expo Go app from App Store
2. Ensure phone is on same WiFi as computer
3. Scan QR code from `npm start` output with camera app
4. Opens in Expo Go automatically!

---

## Understanding the Project

### App Flow

When you start the app:

```
App starts
  ↓
app.tsx: Check if user logged in before
  ↓
If logged in: Show HomeScreen (dashboard)
If not logged in: Show LoginScreen (form)
  ↓
User enters email/password
  ↓
LoginScreen calls: store.login()
  ↓
store.login() calls: apiClient.login()
  ↓
apiClient.login() sends to: http://localhost:8000/api/mobile/auth/login
  ↓
Backend returns tokens
  ↓
Tokens saved to secure storage
  ↓
App shows HomeScreen
```

### Key Files Explained

**app.tsx** (5 KB)
- Main entry point
- Checks if user is logged in
- Shows LoginScreen or HomeScreen

**screens/LoginScreen.tsx** (6 KB)
- Login form
- Input validation
- Calls store.login()

**screens/HomeScreen.tsx** (7 KB)
- Dashboard after login
- Shows financial summary
- Displays sync status
- Logout button

**services/api.ts** (20 KB) ⭐ IMPORTANT
- All API communication
- 20+ methods for different endpoints
- Automatic token refresh
- Error handling
- Each method is well-documented

**stores/appStore.ts** (15 KB)
- Global state management
- Authentication state
- User data
- Sync status
- Uses Zustand (simpler than Redux)

**types/index.ts** (12 KB)
- TypeScript type definitions
- Matches Python backend models
- Full type safety

---

## Testing Login

1. Start the backend:
   ```bash
   cd C:\Users\kevth\desktop\projects\accountancy
   uvicorn backend.main:app --reload
   ```

2. Run the mobile app:
   ```bash
   cd mobile-app
   npm start
   npm run android  # or npm run ios
   ```

3. On the login screen, enter any email/password:
   - Email: `test@example.com`
   - Password: `password123`

4. The app will:
   - Send credentials to backend
   - Backend returns tokens (because it accepts any email/password in demo mode)
   - App saves tokens
   - App shows dashboard

---

## Common Issues & Solutions

### Issue: "Cannot find module 'react-native'"

**Solution**: Dependencies not installed
```bash
npm install
```

### Issue: "Metro bundler failed"

**Solution**: Port 19000 is in use
```bash
npm start -- --clear
```

### Issue: "Android emulator won't start"

**Solution**: Use Android Studio to create/manage emulators
- Open Android Studio → Device Manager → Create Virtual Device

### Issue: "Can't connect to backend (Connection refused)"

**Solution**: Check your `.env.local`:
1. Make sure API_BASE_URL matches your computer's IP
2. Ensure backend is running (`uvicorn backend.main:app --reload`)
3. Device must be on same WiFi as computer
4. Check firewall allows port 8000

### Issue: "Login fails with 401 error"

**Solution**:
- Check `.env.local` has correct API_BASE_URL
- Verify backend is running
- Check backend logs for errors
- Backend currently accepts any email/password (demo mode)

### Issue: "App crashes on startup"

**Solution**:
1. Check terminal for error messages
2. Reload app: Press `r` in Metro terminal
3. Clear cache: `npm start -- --clear`
4. Check `console.log` output in Metro terminal

---

## Next Steps (Phase 3)

Phase 3 will add:

1. **Tab Navigation**
   - Transactions tab (view/create)
   - Accounts tab (view details)
   - Settings tab (notification prefs)

2. **Transaction List Screen**
   - Paginated transaction list
   - Pull-to-refresh
   - Filter by date/account

3. **Create Transaction Screen**
   - Form to create new transaction
   - Offline queuing
   - Validation

4. **Account Details Screen**
   - Account balance
   - Recent transactions
   - Account info

5. **Settings Screen**
   - Notification preferences
   - App settings
   - About/version

---

## Useful Commands

```bash
# Start development server
npm start

# Run on Android
npm run android

# Run on iOS
npm run ios

# Run on web (if configured)
npm run web

# Type check
npm run type-check

# Fix TypeScript errors
npm run type-check

# Lint code
npm run lint

# Clear cache
npm start -- --clear

# Rebuild native code (when adding native modules)
npm run prebuild
```

---

## File Size Reference

Don't worry if the project is large:

```
node_modules/        ~800 MB (don't commit to git)
.expo/               ~100 MB (development cache, auto-generated)
android/             ~500 MB (if you prebuild, optional)
ios/                 ~500 MB (if you prebuild, optional)

Your actual code:     ~200 KB (very small!)
```

---

## Git Configuration

Add this to `.gitignore` (if not already there):

```
node_modules/
.expo/
.expo-shared/
dist/
.env.local
ios/
android/
```

This prevents committing large folders to git.

---

## Success Criteria

You're done with Phase 2 when:

✅ `npm install` completes without errors
✅ `npm start` shows Metro bundler running
✅ App launches on emulator/device
✅ Login screen appears
✅ You can see all UI elements

You'll see:
- Login form with email/password inputs
- "Welcome!" text when logged in
- Financial summary (Revenue, Expenses, Net Income)
- Sync status indicator
- Action buttons
- Logout button

---

## Questions?

If you get stuck:

1. **Check error messages** - Terminal shows detailed errors
2. **Read file comments** - Every file is heavily documented
3. **Check MOBILE_DEV_SETUP.md** - General setup guide
4. **Metro terminal** - Scroll up to see full error trace

Good luck! 🚀
