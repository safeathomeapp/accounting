/**
 * TypeScript Type Definitions for Accountancy Mobile App
 *
 * This file defines all the data types used throughout the app.
 * These types match the Python models from the backend, ensuring
 * we send and receive data in the correct format.
 */

// ==========================================
// AUTHENTICATION TYPES
// ==========================================

/**
 * Login Request
 * Sent to backend when user logs in
 * Fields:
 *  - email: User's email address
 *  - password: User's password
 *  - device_id: Unique identifier for this device (prevents token sharing)
 *  - device_name: Human-readable name like "John's iPhone 14"
 *  - device_os: "iOS" or "Android"
 *  - app_version: Version of this app
 */
export interface LoginRequest {
  email: string;
  password: string;
  device_id: string;
  device_name?: string;
  device_os?: string;
  app_version?: string;
}

/**
 * Login Response
 * Received from backend after successful login
 * Fields:
 *  - access_token: Short-lived token (15 mins), use with every API request
 *  - refresh_token: Long-lived token (7 days), use to get new access_token
 *  - user_id: Unique identifier for the logged-in user
 *  - organization_id: Organization this user belongs to
 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user_id: string;
  organization_id: string;
}

/**
 * Current User
 * Represents the logged-in user
 */
export interface CurrentUser {
  id: string;
  email: string;
  organizationId: string;
  organizationName: string;
}

/**
 * Auth State
 * Stored in secure storage on the device
 * Contains tokens and user information
 */
export interface AuthState {
  isAuthenticated: boolean;
  accessToken: string | null;
  refreshToken: string | null;
  user: CurrentUser | null;
  deviceId: string;
}

// ==========================================
// USER & ORGANIZATION TYPES
// ==========================================

/**
 * User Profile
 * Information about the logged-in user
 */
export interface UserProfile {
  user_id: string;
  email: string;
  organization_id: string;
  organization_name: string;
}

/**
 * Organization Summary
 * Financial overview of the organization
 * Used for dashboard display
 */
export interface OrganizationSummary {
  organization_id: string;
  total_revenue: string; // Decimal as string for precision
  total_expenses: string;
  net_income: string;
  last_sync: string; // ISO 8601 timestamp
}

// ==========================================
// TRANSACTION TYPES
// ==========================================

/**
 * Transaction
 * Represents a single financial transaction
 * Fields:
 *  - id: Unique identifier
 *  - amount: Amount in currency (string for decimal precision)
 *  - date: Date of transaction (YYYY-MM-DD)
 *  - description: What this transaction was for
 *  - account: Account name (like "Checking Account" or "Meals")
 *  - status: pending (not synced), synced, or failed
 */
export interface Transaction {
  id: string;
  amount: string;
  date: string;
  description: string;
  account: string;
  status?: 'pending' | 'synced' | 'failed';
}

/**
 * Create Transaction Request
 * Sent to backend when creating a new transaction
 */
export interface CreateTransactionRequest {
  amount: string;
  date: string;
  description: string;
  account_id: string;
  category_id?: string;
}

/**
 * Transaction List Response
 * Received from backend when listing transactions
 * Always paginated to avoid sending huge amounts of data
 */
export interface TransactionListResponse {
  transactions: Transaction[];
  page: number;
  limit: number;
  total: number;
}

// ==========================================
// ACCOUNT TYPES
// ==========================================

/**
 * Account
 * Represents a bank/credit card account
 * Fields:
 *  - id: Unique identifier
 *  - name: Account name (like "Checking Account")
 *  - balance: Current balance (string for decimal precision)
 */
export interface Account {
  id: string;
  name: string;
  balance: string;
}

/**
 * Account Details
 * Full information about an account
 * Includes transaction history and more details
 */
export interface AccountDetails extends Account {
  last_transaction: string; // ISO 8601 timestamp
}

/**
 * Accounts List Response
 * Received from backend when listing accounts
 */
export interface AccountsListResponse {
  accounts: Account[];
}

// ==========================================
// OFFLINE SYNC TYPES
// ==========================================

/**
 * Sync Queue Item
 * Represents a transaction waiting to be synced to server
 * Used for offline-first architecture
 *
 * Lifecycle:
 * 1. User creates transaction while offline -> status = "pending"
 * 2. App tries to sync -> status = "syncing"
 * 3. Server confirms -> status = "synced" (item removed from queue)
 * 4. If server rejects -> status = "conflict" (user must fix manually)
 * 5. If network error -> status = "failed" (will retry automatically)
 */
export interface SyncQueueItem {
  id?: string;
  action: 'create' | 'update' | 'delete';
  entity_type: string; // "transaction", "account", etc
  entity_data: Record<string, any>;
  status: 'pending' | 'syncing' | 'synced' | 'conflict' | 'failed';
  created_at?: string;
  error?: string;
}

/**
 * Sync Queue Status
 * Summary of what's waiting to sync
 */
export interface SyncQueueStatus {
  pending: number; // Count of pending items
  failed: number; // Count of failed items
  items?: SyncQueueItem[];
}

/**
 * Sync Result
 * Result after trying to sync
 */
export interface SyncResult {
  synced: number; // Count successfully synced
  failed: number; // Count that failed
  message: string;
}

// ==========================================
// PUSH NOTIFICATION TYPES
// ==========================================

/**
 * Push Device Token
 * Device token for receiving push notifications
 * Received from Expo and sent to backend
 */
export interface PushDeviceToken {
  token: string; // Looks like: exponentPushToken[abc123...]
  token_type: 'expo' | 'fcm' | 'apns';
  device_id: string;
  device_name?: string;
  device_os?: string;
}

/**
 * Push Notification
 * A notification received by the device
 * Stored in notification history
 */
export interface PushNotification {
  id: string;
  type: 'sync_complete' | 'alert' | 'info' | 'report';
  title: string;
  body: string;
  received_at: string; // ISO 8601 timestamp
  opened: boolean;
}

/**
 * Notification History
 * List of recent notifications
 */
export interface NotificationHistory {
  notifications: PushNotification[];
}

// ==========================================
// SYNC STATUS TYPES
// ==========================================

/**
 * Sync Status
 * Current state of data synchronization
 */
export interface SyncStatus {
  status: 'synced' | 'syncing' | 'offline' | 'error';
  last_sync: string; // ISO 8601 timestamp
  pending_items: number; // Count of items waiting to sync
}

// ==========================================
// API ERROR TYPES
// ==========================================

/**
 * API Error Response
 * Returned by backend when something goes wrong
 */
export interface ApiError {
  error: string;
  message: string;
  detail?: string;
  status_code: number;
}

/**
 * App Error
 * Structured error for app-level error handling
 */
export interface AppError {
  code: string; // Error code like "AUTH_FAILED", "NETWORK_ERROR"
  message: string; // Human-readable error message
  timestamp: Date;
  originalError?: Error;
}

// ==========================================
// STORE/STATE TYPES
// ==========================================

/**
 * App State
 * Global state of the entire application
 * Managed by Zustand
 */
export interface AppState {
  // Authentication
  auth: AuthState;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;

  // User Data
  user: CurrentUser | null;
  organization: OrganizationSummary | null;

  // Sync Status
  syncStatus: SyncStatus;
  updateSyncStatus: () => Promise<void>;

  // Offline Queue
  syncQueue: SyncQueueItem[];
  addToQueue: (item: SyncQueueItem) => Promise<void>;
  syncQueue: () => Promise<void>;

  // Error Handling
  error: AppError | null;
  clearError: () => void;
}
