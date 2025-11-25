/**
 * App State Store (Zustand)
 *
 * This manages global application state like:
 * - Authentication (login/logout/tokens)
 * - User profile information
 * - Sync status and offline queue
 * - Error messages
 *
 * Zustand is a lightweight state management library that's perfect for React Native.
 * It's simpler than Redux but powerful enough for most apps.
 *
 * Usage:
 *   import { useAppStore } from '@stores/appStore';
 *
 *   // In a component:
 *   export function LoginScreen() {
 *     const { auth, login } = useAppStore();
 *
 *     return (
 *       <Button
 *         onPress={() => login(email, password)}
 *         disabled={!auth.isAuthenticated}
 *       />
 *     );
 *   }
 */

import { create } from 'zustand';
import { apiClient } from '../services/api';
import { AuthState, CurrentUser, OrganizationSummary, AppError, SyncStatus } from '../types';

/**
 * App Store Definition
 *
 * This is the global state that's accessible from any component
 */
interface AppStoreState {
  // =========================================================================
  // AUTHENTICATION STATE
  // =========================================================================

  /**
   * auth: The current authentication state
   *
   * Fields:
   *   - isAuthenticated: True if user is logged in
   *   - accessToken: Current access token (expires in 15 mins)
   *   - refreshToken: Refresh token (expires in 7 days)
   *   - user: Logged-in user's info
   *   - deviceId: Unique device identifier
   */
  auth: AuthState;

  /**
   * login: Authenticate user
   *
   * Args:
   *   email: User's email
   *   password: User's password
   *   deviceId: Unique device identifier
   *   deviceName: Human-readable device name
   *   deviceOs: 'iOS' or 'Android'
   *
   * Throws:
   *   Error if login fails
   *
   * Example:
   *   try {
   *     await login('user@example.com', 'password', 'device-123', "John's iPhone", 'iOS');
   *   } catch (error) {
   *     showErrorMessage(error.message);
   *   }
   */
  login: (
    email: string,
    password: string,
    deviceId: string,
    deviceName?: string,
    deviceOs?: string
  ) => Promise<void>;

  /**
   * logout: Revoke the current session
   *
   * Clears all stored authentication data
   *
   * Example:
   *   const { logout } = useAppStore();
   *   <Button onPress={() => logout()} />
   */
  logout: () => Promise<void>;

  /**
   * refreshToken: Get a new access token
   *
   * Called automatically when token expires
   * You rarely need to call this manually
   */
  refreshToken: () => Promise<void>;

  /**
   * restoreSession: Restore previous session from storage
   *
   * Call this when app starts up
   *
   * Returns:
   *   boolean - true if session was restored, false if user needs to log in
   */
  restoreSession: () => Promise<boolean>;

  // =========================================================================
  // USER DATA
  // =========================================================================

  /**
   * currentUser: Logged-in user's information
   */
  currentUser: CurrentUser | null;

  /**
   * organizationSummary: Financial overview of the organization
   * Used to display dashboard numbers
   */
  organizationSummary: OrganizationSummary | null;

  /**
   * fetchUserProfile: Load user profile from backend
   *
   * Called after login to get user information
   */
  fetchUserProfile: () => Promise<void>;

  /**
   * fetchOrganizationSummary: Load financial summary from backend
   *
   * Called when dashboard is opened
   */
  fetchOrganizationSummary: () => Promise<void>;

  // =========================================================================
  // SYNC STATUS
  // =========================================================================

  /**
   * syncStatus: Current synchronization state
   *
   * Fields:
   *   - status: 'synced', 'syncing', 'offline', or 'error'
   *   - last_sync: ISO timestamp of last successful sync
   *   - pending_items: Count of items waiting to sync
   */
  syncStatus: SyncStatus | null;

  /**
   * updateSyncStatus: Fetch current sync state from backend
   *
   * Call this when app comes online or periodically
   */
  updateSyncStatus: () => Promise<void>;

  /**
   * syncOfflineQueue: Process all pending offline items
   *
   * Called when device comes online
   */
  syncOfflineQueue: () => Promise<void>;

  // =========================================================================
  // ERROR HANDLING
  // =========================================================================

  /**
   * error: Current error message (if any)
   *
   * Shown in error banner/modal to user
   */
  error: AppError | null;

  /**
   * setError: Set an error message
   *
   * Args:
   *   code: Error code (used for handling)
   *   message: Human-readable error message
   *
   * Example:
   *   setError('NETWORK_ERROR', 'No internet connection');
   */
  setError: (code: string, message: string) => void;

  /**
   * clearError: Clear the current error
   *
   * Call this when user taps "OK" on error dialog
   */
  clearError: () => void;
}

/**
 * Create the Zustand store
 *
 * This creates the global state that components can subscribe to
 */
export const useAppStore = create<AppStoreState>((set, get) => ({
  // =========================================================================
  // INITIAL STATE
  // =========================================================================

  auth: {
    isAuthenticated: false,
    accessToken: null,
    refreshToken: null,
    user: null,
    deviceId: '',
  },

  currentUser: null,
  organizationSummary: null,
  syncStatus: null,
  error: null,

  // =========================================================================
  // AUTHENTICATION METHODS
  // =========================================================================

  login: async (email, password, deviceId, deviceName, deviceOs) => {
    try {
      // Call backend API to authenticate
      const response = await apiClient.login({
        email,
        password,
        device_id: deviceId,
        device_name: deviceName,
        device_os: deviceOs,
        app_version: '0.1.0',
      });

      // Update store with new tokens and user info
      set({
        auth: {
          isAuthenticated: true,
          accessToken: response.access_token,
          refreshToken: response.refresh_token,
          user: {
            id: response.user_id,
            email: email,
            organizationId: response.organization_id,
            organizationName: 'Your Organization', // TODO: Get from response
          },
          deviceId,
        },
        error: null,
      });

      // Load user profile data
      const store = get();
      await store.fetchUserProfile();
      await store.fetchOrganizationSummary();
    } catch (error: any) {
      set({
        error: {
          code: 'LOGIN_FAILED',
          message: error.response?.data?.message || 'Login failed. Check your email and password.',
          timestamp: new Date(),
          originalError: error,
        },
      });
      throw error;
    }
  },

  logout: async () => {
    try {
      // Tell backend to revoke the session
      await apiClient.logout();
    } catch (error) {
      console.warn('Logout API failed:', error);
      // Continue with local logout even if API fails
    } finally {
      // Clear all local data
      set({
        auth: {
          isAuthenticated: false,
          accessToken: null,
          refreshToken: null,
          user: null,
          deviceId: '',
        },
        currentUser: null,
        organizationSummary: null,
        syncStatus: null,
        error: null,
      });
    }
  },

  refreshToken: async () => {
    try {
      // This is called automatically by the API client interceptor
      // But we can also call it manually if needed
      const store = get();
      if (!store.auth.refreshToken) {
        throw new Error('No refresh token available');
      }

      // The API client handles the actual refresh
      // Just update our store if needed
    } catch (error: any) {
      set({
        error: {
          code: 'TOKEN_REFRESH_FAILED',
          message: 'Session expired. Please log in again.',
          timestamp: new Date(),
          originalError: error,
        },
      });
      throw error;
    }
  },

  restoreSession: async () => {
    try {
      // Try to load tokens from secure storage
      const tokenLoaded = await apiClient.loadTokens();

      if (tokenLoaded && apiClient.isAuthenticated()) {
        // Try to verify tokens still work by fetching profile
        const profile = await apiClient.getUserProfile();

        set({
          auth: {
            isAuthenticated: true,
            accessToken: null, // Managed by API client
            refreshToken: null, // Managed by API client
            user: {
              id: profile.user_id,
              email: profile.email,
              organizationId: profile.organization_id,
              organizationName: profile.organization_name,
            },
            deviceId: 'restored',
          },
          currentUser: {
            id: profile.user_id,
            email: profile.email,
            organizationId: profile.organization_id,
            organizationName: profile.organization_name,
          },
        });

        return true;
      }

      return false;
    } catch (error) {
      console.warn('Failed to restore session:', error);
      return false;
    }
  },

  // =========================================================================
  // USER DATA METHODS
  // =========================================================================

  fetchUserProfile: async () => {
    try {
      const profile = await apiClient.getUserProfile();
      set({
        currentUser: {
          id: profile.user_id,
          email: profile.email,
          organizationId: profile.organization_id,
          organizationName: profile.organization_name,
        },
      });
    } catch (error: any) {
      console.error('Failed to fetch user profile:', error);
      set({
        error: {
          code: 'FETCH_PROFILE_FAILED',
          message: 'Failed to load user profile',
          timestamp: new Date(),
          originalError: error,
        },
      });
    }
  },

  fetchOrganizationSummary: async () => {
    try {
      const summary = await apiClient.getOrganizationSummary();
      set({ organizationSummary: summary });
    } catch (error: any) {
      console.error('Failed to fetch organization summary:', error);
      // Don't show error to user - this is not critical
    }
  },

  // =========================================================================
  // SYNC METHODS
  // =========================================================================

  updateSyncStatus: async () => {
    try {
      const status = await apiClient.getSyncStatus();
      set({ syncStatus: status });
    } catch (error: any) {
      console.warn('Failed to update sync status:', error);
      // If we can't reach the server, assume we're offline
      set({
        syncStatus: {
          status: 'offline',
          last_sync: new Date().toISOString(),
          pending_items: 0,
        },
      });
    }
  },

  syncOfflineQueue: async () => {
    try {
      const result = await apiClient.syncQueue();
      console.log(`Synced: ${result.synced}, Failed: ${result.failed}`);

      // Update sync status after syncing
      const store = get();
      await store.updateSyncStatus();
    } catch (error: any) {
      console.error('Sync failed:', error);
      set({
        error: {
          code: 'SYNC_FAILED',
          message: 'Failed to sync. Will retry when online.',
          timestamp: new Date(),
          originalError: error,
        },
      });
    }
  },

  // =========================================================================
  // ERROR HANDLING
  // =========================================================================

  setError: (code, message) => {
    set({
      error: {
        code,
        message,
        timestamp: new Date(),
      },
    });
  },

  clearError: () => {
    set({ error: null });
  },
}));
