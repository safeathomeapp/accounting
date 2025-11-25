/**
 * Home Screen
 *
 * This is the main screen shown after login.
 *
 * It displays:
 * - Financial summary (total revenue, expenses, net income)
 * - Sync status indicator
 * - Quick action buttons
 * - Logout button
 *
 * This is a simplified home screen to get you started.
 * In Phase 3, we'll add tab navigation and more screens.
 */

import React, { useEffect, useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  SafeAreaView,
  Alert,
} from 'react-native';
import { useAppStore } from '../stores/appStore';

/**
 * HomeScreen Component
 *
 * Displays the main app interface after login
 */
export default function HomeScreen() {
  // Get data from global store
  const {
    currentUser,
    organizationSummary,
    syncStatus,
    logout,
    fetchOrganizationSummary,
    updateSyncStatus,
    syncOfflineQueue,
  } = useAppStore();

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * useEffect: Load data when screen first loads
   *
   * Fetches:
   * 1. Organization financial summary
   * 2. Sync status
   */
  useEffect(() => {
    const loadData = async () => {
      try {
        console.log('[HomeScreen] Loading data...');
        setIsLoading(true);

        await Promise.all([
          fetchOrganizationSummary(),
          updateSyncStatus(),
        ]);

        console.log('[HomeScreen] Data loaded successfully');
      } catch (error) {
        console.error('[HomeScreen] Error loading data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  /**
   * Handle Pull-to-Refresh
   *
   * When user pulls down the screen, refresh the data
   */
  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      await Promise.all([
        fetchOrganizationSummary(),
        updateSyncStatus(),
      ]);
    } catch (error) {
      console.error('[HomeScreen] Refresh failed:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  /**
   * Handle Sync Offline Queue
   *
   * Manually trigger sync of offline items
   */
  const handleManualSync = async () => {
    try {
      console.log('[HomeScreen] Syncing offline queue...');
      await syncOfflineQueue();
      Alert.alert('Success', 'Sync completed successfully');
      await updateSyncStatus();
    } catch (error: any) {
      Alert.alert('Sync Failed', error.message || 'Failed to sync offline items');
    }
  };

  /**
   * Handle Logout
   *
   * Confirm and log out the user
   */
  const handleLogout = () => {
    Alert.alert(
      'Confirm Logout',
      'Are you sure you want to log out?',
      [
        { text: 'Cancel', onPress: () => {}, style: 'cancel' },
        {
          text: 'Logout',
          onPress: async () => {
            try {
              await logout();
              console.log('[HomeScreen] Logged out successfully');
            } catch (error) {
              Alert.alert('Error', 'Failed to log out');
            }
          },
          style: 'destructive',
        },
      ]
    );
  };

  /**
   * Get color for sync status indicator
   *
   * Green if synced, yellow if syncing, red if offline
   */
  const getSyncStatusColor = (status: string): string => {
    switch (status) {
      case 'synced':
        return '#34C759'; // Green
      case 'syncing':
        return '#FF9500'; // Orange
      case 'offline':
        return '#FF3B30'; // Red
      case 'error':
        return '#FF3B30'; // Red
      default:
        return '#999';
    }
  };

  /**
   * Get human-readable sync status text
   */
  const getSyncStatusText = (status: string): string => {
    switch (status) {
      case 'synced':
        return 'All data synced';
      case 'syncing':
        return 'Syncing...';
      case 'offline':
        return 'Offline mode';
      case 'error':
        return 'Sync error';
      default:
        return 'Unknown';
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} />
        }
      >
        {/* Header with User Info */}
        <View style={styles.header}>
          <Text style={styles.greeting}>
            Welcome, {currentUser?.email?.split('@')[0] || 'User'}!
          </Text>
          <Text style={styles.organization}>
            {currentUser?.organizationName || 'Your Organization'}
          </Text>
        </View>

        {/* Loading Indicator */}
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#007AFF" />
            <Text style={styles.loadingText}>Loading data...</Text>
          </View>
        ) : (
          <>
            {/* Sync Status Card */}
            {syncStatus && (
              <View style={styles.card}>
                <View style={styles.syncStatusHeader}>
                  <View
                    style={[
                      styles.syncStatusIndicator,
                      {
                        backgroundColor: getSyncStatusColor(syncStatus.status),
                      },
                    ]}
                  />
                  <View style={styles.syncStatusInfo}>
                    <Text style={styles.syncStatusText}>
                      {getSyncStatusText(syncStatus.status)}
                    </Text>
                    {syncStatus.pending_items > 0 && (
                      <Text style={styles.pendingText}>
                        {syncStatus.pending_items} items waiting to sync
                      </Text>
                    )}
                  </View>
                </View>

                {syncStatus.status === 'offline' && (
                  <TouchableOpacity
                    style={styles.syncButton}
                    onPress={handleManualSync}
                  >
                    <Text style={styles.syncButtonText}>Sync Now</Text>
                  </TouchableOpacity>
                )}
              </View>
            )}

            {/* Financial Summary Card */}
            {organizationSummary && (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Financial Summary</Text>

                <View style={styles.summaryRow}>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryLabel}>Revenue</Text>
                    <Text style={[styles.summaryValue, styles.positiveValue]}>
                      ${organizationSummary.total_revenue}
                    </Text>
                  </View>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryLabel}>Expenses</Text>
                    <Text style={[styles.summaryValue, styles.negativeValue]}>
                      ${organizationSummary.total_expenses}
                    </Text>
                  </View>
                </View>

                <View style={styles.divider} />

                <View style={styles.summaryRow}>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryLabel}>Net Income</Text>
                    <Text style={[styles.summaryValue, styles.netValue]}>
                      ${organizationSummary.net_income}
                    </Text>
                  </View>
                </View>
              </View>
            )}

            {/* Quick Actions Card */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Quick Actions</Text>

              <TouchableOpacity style={styles.actionButton}>
                <Text style={styles.actionButtonText}>View Transactions</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.actionButton}>
                <Text style={styles.actionButtonText}>Create Transaction</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.actionButton}>
                <Text style={styles.actionButtonText}>View Accounts</Text>
              </TouchableOpacity>
            </View>
          </>
        )}

        {/* Logout Button */}
        <TouchableOpacity
          style={styles.logoutButton}
          onPress={handleLogout}
        >
          <Text style={styles.logoutButtonText}>Logout</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

/**
 * Styles for the Home Screen
 */
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },

  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },

  // ============= HEADER =============
  header: {
    marginBottom: 24,
  },

  greeting: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },

  organization: {
    fontSize: 16,
    color: '#666',
  },

  // ============= LOADING =============
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },

  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#666',
  },

  // ============= CARD =============
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },

  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 16,
  },

  // ============= SYNC STATUS =============
  syncStatusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  syncStatusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },

  syncStatusInfo: {
    flex: 1,
  },

  syncStatusText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },

  pendingText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },

  syncButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
    marginTop: 12,
  },

  syncButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },

  // ============= SUMMARY =============
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },

  summaryItem: {
    flex: 1,
  },

  summaryLabel: {
    fontSize: 12,
    color: '#999',
    marginBottom: 4,
  },

  summaryValue: {
    fontSize: 20,
    fontWeight: 'bold',
  },

  positiveValue: {
    color: '#34C759', // Green
  },

  negativeValue: {
    color: '#FF3B30', // Red
  },

  netValue: {
    color: '#007AFF', // Blue
  },

  divider: {
    height: 1,
    backgroundColor: '#f0f0f0',
    marginVertical: 12,
  },

  // ============= ACTIONS =============
  actionButton: {
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 10,
  },

  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },

  // ============= LOGOUT =============
  logoutButton: {
    backgroundColor: '#FF3B30',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },

  logoutButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
});
