# 🌍 Location Switching Guide

## Overview

You work from two different locations with different IP addresses:
- **Location 1**: `192.168.1.143`
- **Location 2**: `192.168.0.37`

This guide explains how to easily switch between them.

---

## ✅ What's Already Set Up

You now have:

```
mobile-app/
├── .env.location1              Location 1 configuration
├── .env.location2              Location 2 configuration
├── .env.local                  Your active configuration (switches between above)
├── switch-location.bat         Helper script for Windows
└── switch-location.sh          Helper script for Mac/Linux
```

---

## 📋 Initial Setup

### Step 1: Create Initial .env.local

When you first run `npm install`, you need to have `.env.local` set up.

**On Windows**:
```bash
cd mobile-app
switch-location.bat location1
```

**On Mac/Linux**:
```bash
cd mobile-app
chmod +x switch-location.sh
./switch-location.sh location1
```

This copies `.env.location1` to `.env.local` and you're ready to go!

---

## 🔄 Switching Between Locations

### Method 1: Using Helper Scripts (Easiest!)

**When you arrive at Location 2**:

On Windows:
```bash
cd mobile-app
switch-location.bat location2
```

On Mac/Linux:
```bash
cd mobile-app
./switch-location.sh location2
```

Script will tell you:
```
SUCCESS: Switched to Location 2
API_BASE_URL=http://192.168.0.37:8000/api/mobile

Next steps:
  1. Stop npm start (Ctrl+C)
  2. Run: npm start
```

Then just restart your development server and you're done!

---

### Method 2: Manual Copy (No Script)

If you prefer not to use scripts:

**On Windows (Command Prompt)**:
```bash
cd mobile-app
copy .env.location2 .env.local
```

**On Windows (PowerShell)**:
```bash
cd mobile-app
Copy-Item .env.location2 -Destination .env.local
```

**On Mac/Linux**:
```bash
cd mobile-app
cp .env.location2 .env.local
```

---

## 🔍 Check Current Location

### Using Script

**On Windows**:
```bash
switch-location.bat
```

**On Mac/Linux**:
```bash
./switch-location.sh
```

Output:
```
Current .env.local:
API_BASE_URL=http://192.168.1.143:8000/api/mobile
```

### Manual Check

```bash
# Show the current API_BASE_URL
grep API_BASE_URL .env.local
```

Output:
```
API_BASE_URL=http://192.168.1.143:8000/api/mobile
```

---

## 🚀 Complete Workflow Example

### Morning at Location 1

```bash
cd mobile-app

# Check which location is active
switch-location.bat

# Start development
npm start

# In another terminal, run the app
npm run android
```

### Afternoon - Moving to Location 2

```bash
# Stop npm start (press Ctrl+C)

# Switch location
cd mobile-app
switch-location.bat location2

# Restart development
npm start

# App now uses 192.168.0.37
```

### Next Day - Back to Location 1

```bash
# Stop npm start (press Ctrl+C)

# Switch location
cd mobile-app
switch-location.bat location1

# Restart development
npm start

# App now uses 192.168.1.143
```

---

## 📝 Environment File Contents

### .env.location1
```env
API_BASE_URL=http://192.168.1.143:8000/api/mobile
ENVIRONMENT=development
DEBUG=true
API_TIMEOUT=30000
ENABLE_OFFLINE_SYNC=true
ENABLE_PUSH_NOTIFICATIONS=true
```

### .env.location2
```env
API_BASE_URL=http://192.168.0.37:8000/api/mobile
ENVIRONMENT=development
DEBUG=true
API_TIMEOUT=30000
ENABLE_OFFLINE_SYNC=true
ENABLE_PUSH_NOTIFICATIONS=true
```

### .env.local (Active Configuration)
This file is created by copying either `.env.location1` or `.env.location2`.

**IMPORTANT**: `.env.local` is in `.gitignore` - it's never committed to git!

---

## ⚙️ What to Change If Needed

### If IP Addresses Change

Edit the location files:

**On Windows**:
```bash
# Open in Notepad
notepad .env.location1

# Change API_BASE_URL to new IP
API_BASE_URL=http://192.168.1.100:8000/api/mobile

# Save and close
```

**On Mac/Linux**:
```bash
# Open in nano
nano .env.location1

# Edit the API_BASE_URL line
# Press Ctrl+X to save and exit
```

### If Backend Port Changes

If your backend moves from port 8000 to 8001:

```env
# Change from:
API_BASE_URL=http://192.168.1.143:8000/api/mobile

# To:
API_BASE_URL=http://192.168.1.143:8001/api/mobile
```

---

## 🔧 Troubleshooting

### App can't connect to backend after switching

**Solution**:
1. Make sure you switched the `.env.local` file
2. Confirm the IP address is correct for your location
3. Restart `npm start` (not just reload in browser)
4. Check that your backend is running at that IP

**To verify**:
```bash
# Check which location is configured
grep API_BASE_URL .env.local

# Try to ping the IP
ping 192.168.1.143
ping 192.168.0.37
```

### "Cannot find switch-location.bat on Mac"

**Solution**: You're on Mac/Linux, use the `.sh` script instead:
```bash
chmod +x switch-location.sh
./switch-location.sh location1
```

### "Permission denied" when running .sh script

**Solution**: Make it executable first:
```bash
chmod +x switch-location.sh
./switch-location.sh location1
```

### Backend not responding after switching

**Checklist**:
1. ✓ Did you run the switch script/copy command?
2. ✓ Did you restart `npm start`?
3. ✓ Is your backend running at the new location?
4. ✓ Are both computers on the same WiFi?
5. ✓ Is the IP address correct for this location?

---

## 📱 Quick Reference

### Windows
```bash
# Check current location
switch-location.bat

# Switch to Location 1
switch-location.bat location1

# Switch to Location 2
switch-location.bat location2
```

### Mac/Linux
```bash
# Check current location
./switch-location.sh

# Switch to Location 1
./switch-location.sh location1

# Switch to Location 2
./switch-location.sh location2
```

### After Switching
```bash
# Stop current dev server (Ctrl+C)

# Restart dev server
npm start

# App now uses the new location!
```

---

## 🎯 Best Practices

1. **Always check before starting work**
   ```bash
   switch-location.bat
   # or
   ./switch-location.sh
   ```

2. **Switch before restarting npm**
   - Switch location first
   - Then restart `npm start`

3. **Don't manually edit .env.local**
   - Edit `.env.location1` or `.env.location2` instead
   - Use the script to activate them

4. **Keep both .env.location* files in sync**
   - Only the `API_BASE_URL` should differ
   - Other settings should be the same

---

## 🚀 Bonus: Add to Your Workflow

### Windows: Create a batch file for quick setup

Create `morning-setup.bat`:
```batch
@echo off
cd mobile-app
echo Checking location...
switch-location.bat
echo.
echo Starting development server...
npm start
```

Then just double-click it in the morning!

### Mac/Linux: Create a shell script for quick setup

Create `morning-setup.sh`:
```bash
#!/bin/bash
cd mobile-app
echo "Checking location..."
./switch-location.sh
echo ""
echo "Starting development server..."
npm start
```

Then:
```bash
chmod +x morning-setup.sh
./morning-setup.sh
```

---

## ✨ Summary

You have a clean, simple system for managing two locations:

✅ Two environment files (.env.location1, .env.location2)
✅ One active file (.env.local)
✅ Helper scripts to switch between them
✅ No manual IP editing needed
✅ Works on Windows, Mac, and Linux
✅ Scales well if you add more locations later

**That's it!** You're all set for working from two locations. 🎉
