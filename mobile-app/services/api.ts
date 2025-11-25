/**
 * API Client Service for Accountancy Mobile App
 *
 * This service handles all communication with the backend API.
 *
 * Key responsibilities:
 * 1. Making HTTP requests to backend
 * 2. Managing authentication tokens (adding them to headers)
 * 3. Handling errors and retries
 * 4. Refreshing expired tokens automatically
 * 5. Queuing requests when offline
 *
 * How it works:
 * - Every API request includes the access_token in the Authorization header
 * - If we get a 401 (token expired), we automatically refresh it
 * - If the request fails due to network, we can queue it for later
 * - All responses are typed with TypeScript for safety
 */

import axios, {
  AxiosInstance,
  AxiosError,
  AxiosRequestConfig,
  AxiosResponse,
} from 'axios';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  LoginRequest,
  LoginResponse,
  UserProfile,
  OrganizationSummary,
  Transaction,
  TransactionListResponse,
  CreateTransactionRequest,
  Account,
  AccountsListResponse,
  AccountDetails,
  SyncQueueStatus,
  SyncResult,
  PushDeviceToken,
  NotificationHistory,
  SyncStatus,
  ApiError,
} from '../types';

/**
 * API Client Class
 *
 * Usage:
 *   const api = new ApiClient('http://localhost:8000/api/mobile');
 *   const profile = await api.getUserProfile();
 */
export class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  /**
   * Constructor
   *
   * Sets up the HTTP client with proper headers and interceptors
   *
   * Args:
   *   baseURL: The base URL of the backend API
   *            Example: 'http://localhost:8000/api/mobile'
   */
  constructor(baseURL: string) {
    this.baseURL = baseURL;

    // Create axios instance with default config
    this.client = axios.create({
      baseURL,
      timeout: 30000, // 30 second timeout
      headers: {
        'Content-Type': 'application/json',
        // User-Agent helps backend identify mobile app
        'User-Agent': 'AccountancyMobile/0.1.0',
      },
    });

    // Add request interceptor to attach token to every request
    this.client.interceptors.request.use(
      (config) => {
        // If we have an access token, add it to the Authorization header
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor to handle 401 errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & {
          _retry?: boolean;
        };

        // If we get a 401 (Unauthorized), try refreshing the token
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            // Try to get a new access token using the refresh token
            await this.refreshAccessToken();

            // Retry the original request with new token
            if (this.accessToken && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${this.accessToken}`;
            }
            return this.client(originalRequest);
          } catch (refreshError) {
            // If refresh fails, the user needs to log in again
            await this.logout();
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  /**
   * Load saved tokens from secure storage
   *
   * Called on app startup to restore the previous session
   * Tokens are stored securely on the device
   */
  async loadTokens(): Promise<boolean> {
    try {
      const accessToken = await SecureStore.getItemAsync('accessToken');
      const refreshToken = await SecureStore.getItemAsync('refreshToken');

      if (accessToken && refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        return true;
      }
    } catch (error) {
      console.error('Failed to load tokens from secure storage:', error);
    }

    return false;
  }

  /**
   * Save tokens to secure storage
   *
   * Called after successful login or token refresh
   * Never store tokens in regular AsyncStorage - it's not secure!
   */
  private async saveTokens(
    accessToken: string,
    refreshToken: string
  ): Promise<void> {
    try {
      await SecureStore.setItemAsync('accessToken', accessToken);
      await SecureStore.setItemAsync('refreshToken', refreshToken);
      this.accessToken = accessToken;
      this.refreshToken = refreshToken;
    } catch (error) {
      console.error('Failed to save tokens to secure storage:', error);
      throw error;
    }
  }

  /**
   * Clear tokens from memory and secure storage
   *
   * Called on logout
   */
  private async clearTokens(): Promise<void> {
    try {
      await SecureStore.deleteItemAsync('accessToken');
      await SecureStore.deleteItemAsync('refreshToken');
      this.accessToken = null;
      this.refreshToken = null;
    } catch (error) {
      console.error('Failed to clear tokens:', error);
    }
  }

  // =========================================================================
  // AUTHENTICATION ENDPOINTS
  // =========================================================================

  /**
   * Login
   *
   * Authenticates user and receives access/refresh tokens
   *
   * Args:
   *   request: LoginRequest with email, password, device info
   *
   * Returns:
   *   LoginResponse with tokens and user info
   *
   * Example:
   *   const result = await api.login({
   *     email: 'user@example.com',
   *     password: 'password123',
   *     device_id: 'iPhone_12345',
   *     device_name: "John's iPhone",
   *     device_os: 'iOS',
   *     app_version: '0.1.0'
   *   });
   */
  async login(request: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>(
      '/auth/login',
      request
    );
    const data = response.data;

    // Save tokens for future requests
    await this.saveTokens(data.access_token, data.refresh_token);

    return data;
  }

  /**
   * Refresh Access Token
   *
   * Gets a new access token when the current one expires
   * Called automatically when we get a 401 error
   *
   * Returns:
   *   New access token
   *
   * Note:
   *   This is called automatically by the response interceptor
   *   You rarely need to call this directly
   */
  async refreshAccessToken(): Promise<string> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await this.client.post<LoginResponse>('/auth/refresh', {
      refresh_token: this.refreshToken,
      device_id: await this.getDeviceId(),
    });

    const data = response.data;
    await this.saveTokens(data.access_token, data.refresh_token);

    return data.access_token;
  }

  /**
   * Logout
   *
   * Revokes the session and clears tokens
   * Call this when user taps the Logout button
   *
   * Returns:
   *   boolean indicating success
   */
  async logout(): Promise<void> {
    try {
      // Tell backend to revoke the session
      await this.client.post('/auth/logout');
    } catch (error) {
      console.warn('Logout API call failed:', error);
      // Still clear tokens locally even if API call fails
    } finally {
      // Clear tokens from memory and storage
      await this.clearTokens();
    }
  }

  // =========================================================================
  // USER & ORGANIZATION ENDPOINTS
  // =========================================================================

  /**
   * Get User Profile
   *
   * Fetches information about the logged-in user
   *
   * Returns:
   *   UserProfile with email, user_id, organization info
   *
   * Example:
   *   const profile = await api.getUserProfile();
   *   console.log(profile.email);
   */
  async getUserProfile(): Promise<UserProfile> {
    const response = await this.client.get<UserProfile>('/user/profile');
    return response.data;
  }

  /**
   * Get Organization Summary
   *
   * Fetches financial overview of the organization
   * Used to display dashboard numbers
   *
   * Returns:
   *   OrganizationSummary with revenue, expenses, net income
   *
   * Example:
   *   const summary = await api.getOrganizationSummary();
   *   console.log(`Revenue: ${summary.total_revenue}`);
   */
  async getOrganizationSummary(): Promise<OrganizationSummary> {
    const response = await this.client.get<OrganizationSummary>(
      '/org/summary'
    );
    return response.data;
  }

  // =========================================================================
  // TRANSACTION ENDPOINTS
  // =========================================================================

  /**
   * List Transactions
   *
   * Fetches paginated list of transactions
   * Use pagination to avoid downloading thousands of transactions
   *
   * Args:
   *   page: Page number (1, 2, 3...)
   *   limit: Items per page (default 20)
   *
   * Returns:
   *   TransactionListResponse with transactions array and pagination info
   *
   * Example:
   *   const response = await api.listTransactions(1, 20);
   *   console.log(`Found ${response.total} transactions`);
   *   console.log(response.transactions);
   */
  async listTransactions(
    page: number = 1,
    limit: number = 20
  ): Promise<TransactionListResponse> {
    const response = await this.client.get<TransactionListResponse>(
      '/transactions',
      {
        params: { page, limit },
      }
    );
    return response.data;
  }

  /**
   * Create Transaction
   *
   * Creates a new transaction
   * Can be called online or offline:
   * - Online: Sent immediately to server
   * - Offline: Added to sync queue, sent when online
   *
   * Args:
   *   request: CreateTransactionRequest with amount, date, description, etc
   *
   * Returns:
   *   Response with transaction_id and status
   *
   * Example:
   *   const response = await api.createTransaction({
   *     amount: '50.00',
   *     date: '2025-11-25',
   *     description: 'Lunch',
   *     account_id: 'acc-123',
   *     category_id: 'meals-456'
   *   });
   *   console.log(`Created transaction: ${response.transaction_id}`);
   */
  async createTransaction(
    request: CreateTransactionRequest
  ): Promise<{ transaction_id: string; status: string }> {
    const response = await this.client.post<{
      transaction_id: string;
      status: string;
    }>('/transactions', request);
    return response.data;
  }

  // =========================================================================
  // ACCOUNT ENDPOINTS
  // =========================================================================

  /**
   * List Accounts
   *
   * Fetches all accounts for the organization
   * Used to populate account picker when creating transactions
   *
   * Returns:
   *   AccountsListResponse with accounts array
   *
   * Example:
   *   const response = await api.listAccounts();
   *   response.accounts.forEach(account => {
   *     console.log(`${account.name}: ${account.balance}`);
   *   });
   */
  async listAccounts(): Promise<AccountsListResponse> {
    const response = await this.client.get<AccountsListResponse>('/accounts');
    return response.data;
  }

  /**
   * Get Account Details
   *
   * Fetches details for a specific account
   *
   * Args:
   *   accountId: UUID of the account
   *
   * Returns:
   *   AccountDetails with balance and last transaction info
   *
   * Example:
   *   const details = await api.getAccountDetails('acc-123');
   *   console.log(`Balance: ${details.balance}`);
   */
  async getAccountDetails(accountId: string): Promise<AccountDetails> {
    const response = await this.client.get<AccountDetails>(
      `/accounts/${accountId}`
    );
    return response.data;
  }

  // =========================================================================
  // OFFLINE SYNC ENDPOINTS
  // =========================================================================

  /**
   * Get Sync Queue
   *
   * Fetches what's waiting to be synced to server
   * Useful for displaying sync status to user
   *
   * Returns:
   *   SyncQueueStatus with pending and failed item counts
   *
   * Example:
   *   const queue = await api.getSyncQueue();
   *   if (queue.pending > 0) {
   *     console.log(`${queue.pending} items waiting to sync`);
   *   }
   */
  async getSyncQueue(): Promise<SyncQueueStatus> {
    const response = await this.client.get<SyncQueueStatus>('/sync-queue');
    return response.data;
  }

  /**
   * Add to Sync Queue
   *
   * Adds an item to the offline sync queue
   * Called when user creates a transaction while offline
   *
   * Args:
   *   action: 'create', 'update', or 'delete'
   *   entityType: 'transaction', 'account', etc
   *   entityData: The actual data to sync
   *
   * Returns:
   *   The created queue item
   *
   * Example:
   *   const item = await api.addToSyncQueue('create', 'transaction', {
   *     amount: '50.00',
   *     description: 'Offline transaction'
   *   });
   */
  async addToSyncQueue(
    action: 'create' | 'update' | 'delete',
    entityType: string,
    entityData: Record<string, any>
  ): Promise<{ id: string; status: string }> {
    const response = await this.client.post<{ id: string; status: string }>(
      '/sync-queue',
      {
        action,
        entity_type: entityType,
        entity_data: entityData,
      }
    );
    return response.data;
  }

  /**
   * Sync Queue
   *
   * Processes the sync queue - sends all pending items to server
   * Called when device comes back online
   *
   * Returns:
   *   SyncResult with count of synced and failed items
   *
   * Example:
   *   const result = await api.syncQueue();
   *   console.log(`Synced: ${result.synced}, Failed: ${result.failed}`);
   */
  async syncQueue(): Promise<SyncResult> {
    const response = await this.client.post<SyncResult>('/sync-queue/sync');
    return response.data;
  }

  // =========================================================================
  // PUSH NOTIFICATION ENDPOINTS
  // =========================================================================

  /**
   * Register Push Device
   *
   * Registers this device to receive push notifications
   * Call this when the app starts or when user grants notification permission
   *
   * Args:
   *   token: Push notification token from Expo
   *   deviceId: Unique device identifier
   *   deviceName: Human-readable name
   *   deviceOs: 'iOS' or 'Android'
   *
   * Returns:
   *   Response indicating success
   *
   * Example:
   *   const token = await getExpoToken();
   *   const response = await api.registerPushDevice(
   *     token,
   *     deviceId,
   *     "John's iPhone",
   *     'iOS'
   *   );
   */
  async registerPushDevice(
    token: string,
    deviceId: string,
    deviceName?: string,
    deviceOs?: string
  ): Promise<{ success: boolean; device_id: string }> {
    const response = await this.client.post<{
      success: boolean;
      device_id: string;
    }>('/notifications/register-device', {
      token,
      token_type: 'expo',
      device_id: deviceId,
      device_name: deviceName,
      device_os: deviceOs,
    });
    return response.data;
  }

  /**
   * Get Notification History
   *
   * Fetches recent notifications
   * Useful for displaying notification center
   *
   * Returns:
   *   NotificationHistory with notifications array
   *
   * Example:
   *   const history = await api.getNotificationHistory();
   *   history.notifications.forEach(notif => {
   *     console.log(notif.title);
   *   });
   */
  async getNotificationHistory(): Promise<NotificationHistory> {
    const response = await this.client.get<NotificationHistory>(
      '/notifications/history'
    );
    return response.data;
  }

  // =========================================================================
  // SYNC STATUS ENDPOINTS
  // =========================================================================

  /**
   * Get Sync Status
   *
   * Gets current sync state
   * Used to display sync indicator in UI
   *
   * Returns:
   *   SyncStatus with status and pending items count
   *
   * Example:
   *   const status = await api.getSyncStatus();
   *   if (status.status === 'synced') {
   *     showGreenCheckmark();
   *   }
   */
  async getSyncStatus(): Promise<SyncStatus> {
    const response = await this.client.get<SyncStatus>('/sync/status');
    return response.data;
  }

  // =========================================================================
  // HEALTH CHECK
  // =========================================================================

  /**
   * Health Check
   *
   * Checks if the backend is reachable
   * Call this to detect if device is online
   * Doesn't require authentication
   *
   * Returns:
   *   Response with status
   *
   * Example:
   *   try {
   *     await api.healthCheck();
   *     setIsOnline(true);
   *   } catch (error) {
   *     setIsOnline(false);
   *   }
   */
  async healthCheck(): Promise<{ status: string; api_version: string }> {
    const response = await this.client.get<{
      status: string;
      api_version: string;
    }>('/health');
    return response.data;
  }

  // =========================================================================
  // UTILITY METHODS
  // =========================================================================

  /**
   * Get Device ID
   *
   * Gets a unique identifier for this device
   * Used for device fingerprinting (prevents token sharing)
   *
   * Returns:
   *   A unique device ID
   */
  private async getDeviceId(): Promise<string> {
    try {
      let deviceId = await AsyncStorage.getItem('deviceId');
      if (!deviceId) {
        // Generate a random device ID if we don't have one
        deviceId = `device_${Math.random().toString(36).substr(2, 9)}`;
        await AsyncStorage.setItem('deviceId', deviceId);
      }
      return deviceId;
    } catch (error) {
      console.error('Failed to get device ID:', error);
      return 'unknown_device';
    }
  }

  /**
   * Is Authenticated
   *
   * Quick check to see if we have valid tokens
   *
   * Returns:
   *   boolean
   */
  isAuthenticated(): boolean {
    return this.accessToken !== null && this.refreshToken !== null;
  }
}

// Create a singleton instance
export const apiClient = new ApiClient(
  'http://localhost:8000/api/mobile' // TODO: Use environment variable in production
);
