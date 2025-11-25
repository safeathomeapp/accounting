/**
 * Main App Entry Point
 *
 * This is the root component of the entire application.
 * It handles:
 * 1. Restoring previous user session on startup
 * 2. Displaying loading screen while checking authentication
 * 3. Showing login screen if not authenticated
 * 4. Showing app screens if authenticated
 *
 * Flow:
 * App starts -> Check for saved session -> Show Login or Home -> Navigate based on state
 */

import React, { useEffect, useState } from 'react';
import { StyleSheet, View, ActivityIndicator } from 'react-native';
import * as SplashScreen from 'expo-splash-screen';
import { useAppStore } from './stores/appStore';
import LoginScreen from './screens/LoginScreen';
import HomeScreen from './screens/HomeScreen';

// Keep the splash screen visible while we load the app
SplashScreen.preventAutoHideAsync();

/**
 * Root App Component
 *
 * This component:
 * 1. Checks if user was previously logged in
 * 2. Shows a loading screen while checking
 * 3. Displays either LoginScreen or HomeScreen
 */
export default function App() {
  // Get authentication state and restore session method from Zustand store
  const { auth, restoreSession } = useAppStore();
  const [isReady, setIsReady] = useState(false);

  /**
   * useEffect: Run when app first loads
   *
   * This effect:
   * 1. Tries to restore the previous session from secure storage
   * 2. Hides the splash screen when done
   *
   * This allows the user to stay logged in even after closing the app
   */
  useEffect(() => {
    const bootstrap = async () => {
      try {
        console.log('[App] Checking for saved session...');

        // Try to restore the previous login session
        const sessionRestored = await restoreSession();

        if (sessionRestored) {
          console.log('[App] Session restored from secure storage');
        } else {
          console.log('[App] No previous session found');
        }
      } catch (error) {
        console.error('[App] Error restoring session:', error);
        // Continue with login screen if restore fails
      } finally {
        // Mark the app as ready
        // This is needed for proper navigation
        setIsReady(true);

        // Hide the splash screen now that we've checked authentication
        await SplashScreen.hideAsync();
      }
    };

    bootstrap();
  }, []);

  /**
   * Show loading screen while checking session
   *
   * This prevents showing the wrong screen (login vs home)
   * while we're still checking if a previous session exists
   */
  if (!isReady) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
      </View>
    );
  }

  /**
   * Show LoginScreen if not authenticated
   *
   * User will see the login form and can enter credentials
   */
  if (!auth.isAuthenticated) {
    return <LoginScreen />;
  }

  /**
   * Show HomeScreen if authenticated
   *
   * This is the main app with tabs and navigation
   */
  return <HomeScreen />;
}

/**
 * Styles for the loading screen
 *
 * This is shown while we check for a previous session
 */
const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
});
