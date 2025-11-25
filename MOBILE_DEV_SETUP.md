# 📱 Mobile App Development Setup Guide

**For**: Building React Native app that works on iOS + Android
**Status**: Step-by-step guide with detailed instructions
**Last Updated**: November 25, 2025

---

## 📋 Table of Contents

1. [What You'll Build](#what-youll-build)
2. [Software You Need](#software-you-need)
3. [Backend Setup (Python - I'm doing this)](#backend-setup)
4. [Mobile App Setup (React Native - You'll do this)](#mobile-app-setup)
5. [Testing & Debugging](#testing--debugging)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 What You'll Build

By end of Month 6:

```
✅ Backend API (Python/FastAPI)
   - 20 mobile-optimized endpoints
   - JWT authentication
   - Offline sync queue
   - 52 tests passing

✅ Mobile App (React Native)
   - iOS version (runs on Apple devices)
   - Android version (runs on Android devices)
   - Same codebase for both
   - Login, transactions, sync, notifications

✅ One App → Two Platforms
   - iOS App Store distribution (later)
   - Google Play Store distribution (later)
   - Reach millions of users
```

---

## 💻 Software You Need

### Already Have ✅
- VS Code (for editing code)
- Python 3.13.7
- PostgreSQL
- Git

### Need to Install (Today)

#### 1. Node.js & npm (REQUIRED)
**What**: JavaScript runtime and package manager
**Why**: React Native runs on Node.js

**Install**:
1. Go to: https://nodejs.org/
2. Download: **LTS version** (Long Term Support)
3. Install (next, next, finish)
4. Verify in terminal:
   ```bash
   node --version    # Should show v20.x.x or higher
   npm --version     # Should show 10.x.x or higher
   ```

**If you already have it:**
```bash
node --version
npm --version
```

#### 2. React Native CLI (REQUIRED)
**What**: Command-line tool to create and manage React Native apps
**Why**: Needed to run the app locally

**Install** (in terminal/PowerShell):
```bash
npm install -g react-native-cli expo-cli
```

**Verify**:
```bash
react-native --version
expo --version
```

#### 3. Android Studio (Already Have, Just Need Emulator)
**What**: IDE for Android + comes with emulator
**Status**: You probably already have this from previous work

**Verify Android Emulator Works**:
```bash
# In Android Studio: Tools → Device Manager
# Click: Create Device → Choose Pixel 6 or similar → Create
# Click: ▶ (play) to start emulator
```

**Should see**: Android phone emulator starting up

#### 4. Xcode (For iOS - Optional for Now)
**What**: Apple's IDE for iOS development
**Status**: Only needed if you get Mac or want iOS emulator

**Options**:
- A) Get a Mac (ideal for iOS testing)
- B) Use Expo Go app on friend's iPhone (test without Mac)
- C) Use BrowserStack ($15/mo) for iOS emulator

---

## 🔧 Backend Setup (I'm Building This)

### What I'll Create:

```
backend/
├── models/
│   ├── mobile_session.py           ← JWT token management
│   ├── offline_sync_queue.py       ← Offline transaction queue
│   └── push_notification.py        ← Notification framework
├── api/
│   └── mobile_routes.py            ← 20 mobile endpoints
├── services/
│   ├── mobile_auth.py              ← Authentication logic
│   ├── offline_sync.py             ← Sync queue processing
│   └── notifications.py            ← Notification handling
└── middleware/
    └── mobile_auth_middleware.py   ← JWT validation
```

### Backend Testing:

```bash
# All backend tests will pass
pytest tests/test_mobile_api.py -v           # All 52 tests
pytest tests/test_mobile_auth.py -v          # Auth tests
pytest tests/test_offline_sync.py -v         # Sync tests
pytest tests/test_push_notifications.py -v   # Notification tests
```

### You Don't Need to Build Backend
- I'm handling all Python code
- Just run tests to verify
- Endpoints will be ready for your mobile app

---

## 📱 Mobile App Setup (You'll Do This)

### Step-by-Step Process

#### Step 1: Create React Native Project

```bash
# In terminal, navigate to your accountancy folder
cd C:/Users/kevth/desktop/projects/accountancy

# Create React Native app
npx create-expo-app mobile

# This creates:
mobile/
├── app.json
├── package.json
├── App.tsx              ← Main app file
├── app/
│   └── (screens will go here)
└── ...
```

**Time**: 2-3 minutes
**What it does**: Sets up empty React Native project with Expo (easiest way to test)

#### Step 2: Install Dependencies

```bash
cd mobile
npm install axios react-native-async-storage @react-navigation/native
npm install expo-splash-screen expo-status-bar
```

**What these are**:
- `axios` - For calling your backend API
- `@react-navigation` - For screen navigation
- `react-native-async-storage` - For offline data storage
- `expo-*` - Expo utilities

**Time**: 3-5 minutes

#### Step 3: Copy My React Native Code

I'll provide:
```
mobile/src/
├── screens/
│   ├── LoginScreen.tsx          (Login page)
│   ├── TransactionListScreen.tsx (Transaction list)
│   └── CreateTransactionScreen.tsx (New transaction)
├── services/
│   ├── api.ts                   (Backend communication)
│   ├── auth.ts                  (JWT token management)
│   └── offlineSync.ts           (Offline queue handling)
├── types/
│   └── index.ts                 (TypeScript types)
└── App.tsx                      (Main app entry point)
```

You copy these files into your project:
```bash
# Copy files from my code into mobile/src/
# I'll provide exact copy-paste instructions
```

**Time**: 5 minutes (copy-paste)

#### Step 4: Test Backend & Frontend Together

```bash
# Terminal 1: Start backend
cd C:/Users/kevth/desktop/projects/accountancy
python -m uvicorn backend.main:app --reload

# Terminal 2: Start React Native app
cd mobile
npm start

# This shows you a menu:
# [e] open Android emulator
# [i] open iOS simulator
# [w] open web
# Just press [e] for Android
```

**You'll see**:
- Android emulator opens
- React Native app loads
- Login screen appears
- Test login with: email@example.com / password123

**Time**: 2 minutes

---

## 🧪 Testing & Debugging

### Running Backend Tests

```bash
# Test everything
pytest tests/test_mobile_api.py -v

# Test specific area
pytest tests/test_mobile_auth.py -v         # Auth tests
pytest tests/test_offline_sync.py -v        # Sync tests
pytest tests/test_push_notifications.py -v  # Notification tests

# Should see:
# ✅ test_login_success
# ✅ test_token_refresh
# ✅ test_offline_queue_add
# ... (all 52 tests)
# ============= 52 passed =============
```

### Testing Mobile App

#### Option 1: Android Emulator (Easiest)
```bash
cd mobile
npm start
# Press [e]
# Emulator opens with your app
# Tap buttons to test
# See console logs in terminal
```

#### Option 2: Expo Go App (On Real Device)
```bash
# Download "Expo Go" app (free)
# iOS: App Store
# Android: Google Play Store

npm start
# You'll see QR code in terminal
# Scan with your phone's camera (iOS) or Expo Go app (Android)
# See live app on your phone!
```

#### Option 3: Debugging in VS Code
```bash
# In VS Code, install extension:
# "React Native Tools" by Microsoft

# Then in VS Code:
# Debug → Start Debugging
# Set breakpoints
# Run app and debug like normal
```

---

## 🐛 Troubleshooting

### "Command not found: react-native"

**Problem**: Node.js or CLI not installed

**Solution**:
```bash
# Verify Node.js is installed
node --version

# If error, reinstall from https://nodejs.org/

# Then reinstall CLI
npm install -g react-native-cli expo-cli
```

---

### "Port 8081 already in use"

**Problem**: Another React Native app is running

**Solution**:
```bash
# Option 1: Kill the process
lsof -i :8081  # See what's using port
kill -9 <PID>  # Kill it

# Option 2: Use different port
npm start -- --port 8082
```

---

### "Android emulator won't start"

**Problem**: Android emulator not configured

**Solution**:
1. Open Android Studio
2. Tools → Device Manager
3. Click "Create Device"
4. Select "Pixel 6" (or any recent)
5. Click "Create"
6. Click ▶ (play button) to start

---

### "App crashes on login"

**Problem**: Backend not running or wrong URL

**Solution**:
1. Check backend is running:
   ```bash
   curl http://localhost:8000/health
   # Should see: {"status": "healthy", ...}
   ```

2. Check API URL in mobile app:
   ```typescript
   // In mobile/src/services/api.ts
   const API_URL = "http://10.0.2.2:8000"; // Android emulator
   // or
   const API_URL = "http://localhost:8000"; // Physical device (same network)
   ```

3. See full error in VS Code console

---

### "Token expired error"

**Problem**: JWT token expired (happens after 15 minutes)

**Solution**: Automatic! The app will refresh the token.

If it doesn't:
```typescript
// In mobile/src/services/auth.ts
// Check refresh token logic
console.log("Refreshing token...");
```

---

### "Can't connect to backend from emulator"

**Problem**: Emulator can't reach localhost on your PC

**Solution**:
```bash
# Android emulator uses special IP for localhost:
# Use: 10.0.2.2:8000 (not localhost:8000)

# In mobile app config:
const API_URL = "http://10.0.2.2:8000"; // ✅ Correct for Android emulator
const API_URL = "http://localhost:8000"; // ❌ Won't work for emulator
```

---

### "iOS simulator not working"

**Problem**: Xcode not installed (Mac only)

**Solution**:
```bash
# Option 1: Get a Mac (best for iOS)
# Option 2: Use Expo Go on friend's iPhone
# Option 3: Use BrowserStack iOS emulator ($15/mo)

# For now, just test Android!
# iOS can wait until you have device/Mac
```

---

## 📖 Documentation Strategy

I'll provide **comprehensive comments** in ALL code:

### Example (What you'll see):

```typescript
/**
 * LoginScreen.tsx
 *
 * Screen where user enters email and password to log in.
 *
 * Flow:
 * 1. User enters email + password
 * 2. Presses "Login" button
 * 3. Calls auth service with credentials
 * 4. If successful: JWT token saved locally
 * 5. Navigate to transaction list screen
 * 6. If failed: Show error message
 *
 * Key concepts:
 * - useState: Store form input state
 * - useNavigation: Navigate between screens
 * - asyncStorage: Save token locally (survives app restart)
 */

import React, { useState } from 'react';
import { View, TextInput, Button, Text } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import * as authService from '../services/auth';

export default function LoginScreen() {
  // Store email input (what user types)
  const [email, setEmail] = useState('');

  // Store password input
  const [password, setPassword] = useState('');

  // Track if currently logging in (shows loading spinner)
  const [loading, setLoading] = useState(false);

  // Track error message if login fails
  const [error, setError] = useState('');

  // Hook to navigate to other screens
  const navigation = useNavigation();

  // Function called when user presses "Login" button
  const handleLogin = async () => {
    try {
      setLoading(true);
      setError(''); // Clear previous error

      // Call backend API with email + password
      // This returns: { access_token, refresh_token, user }
      const response = await authService.login(email, password);

      // Save JWT token to phone's local storage
      // This persists even if app is closed
      await authService.saveToken(response.access_token);

      // Navigate to TransactionListScreen
      // User is now logged in!
      navigation.navigate('TransactionList');

    } catch (err) {
      // Show error message if login fails
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ padding: 20 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold' }}>Login</Text>

      {/* Email input field */}
      <TextInput
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        style={{ borderWidth: 1, padding: 10, marginVertical: 10 }}
      />

      {/* Password input field */}
      <TextInput
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry={true}  // Hide password characters
        style={{ borderWidth: 1, padding: 10, marginVertical: 10 }}
      />

      {/* Show error if login failed */}
      {error && <Text style={{ color: 'red' }}>{error}</Text>}

      {/* Login button */}
      <Button
        title={loading ? 'Logging in...' : 'Login'}
        onPress={handleLogin}
        disabled={loading}
      />
    </View>
  );
}
```

**Every file will have**:
- 📝 Purpose explanation
- 🔄 Flow/logic explanation
- 💡 Key concepts noted
- 🐛 Common debugging tips
- 📚 Links to learn more

---

## 🎯 What Happens Next

### I Will Do:
1. ✅ Build complete backend API (Python)
2. ✅ Write 52 comprehensive tests
3. ✅ Create fully documented React Native app code
4. ✅ Add debugging guide for common issues
5. ✅ Commit everything with clear messages

### You Will Do:
1. 📥 Install Node.js + React Native CLI
2. 📱 Create React Native project
3. 📋 Copy code I provide into your project
4. ▶️ Run `npm start` and test
5. 🐛 Debug any issues (I'll help!)

### Time Investment:
- Backend: ~4 hours (I do)
- Setup & testing: ~2 hours (you do)
- Debugging: ~1-2 hours (we do together)
- **Total**: ~8-10 hours across the month

---

## ✅ Success Criteria

By end of Month 6, you'll have:

```
✅ Backend running on http://localhost:8000
   - 20 mobile endpoints working
   - 52 tests passing
   - JWT authentication
   - Offline queue system

✅ React Native app working
   - Login screen functional
   - Transaction list working
   - Can create transactions
   - Works on Android emulator

✅ iOS ready (when you get device/Mac)
   - Same code runs on iOS
   - Just recompile for App Store
   - No code changes needed

✅ Fully documented
   - Every file explained
   - Debugging guide included
   - Ready to extend/modify
```

---

## 🚀 Ready to Start?

Next steps:

1. **Install Node.js**: https://nodejs.org/ (choose LTS)
2. **Install React Native CLI**:
   ```bash
   npm install -g react-native-cli expo-cli
   ```
3. **Verify installations**:
   ```bash
   node --version
   npm --version
   react-native --version
   expo --version
   ```
4. **Tell me you're ready** - I'll start building Phase 1!

---

## 📞 Support

When you get stuck:
1. Check this guide first
2. Check DEBUGGING_GUIDE.md (I'll create it)
3. Run the code I provide
4. Look at console error messages
5. Ask me with the error text

**I'm here to help debug anything that comes up.** That's why I'm writing detailed code with lots of comments and a debugging guide.

---

**Questions before we start?** 🚀

Let me know when you have Node.js installed and I'll begin Phase 1!
