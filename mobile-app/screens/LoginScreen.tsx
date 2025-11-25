/**
 * Login Screen
 *
 * This screen is shown when the user is not logged in.
 *
 * Features:
 * - Email and password form fields
 * - Login button that calls the backend
 * - Error messages if login fails
 * - Loading indicator while logging in
 *
 * After successful login, the app shows the HomeScreen
 */

import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Platform,
  KeyboardAvoidingView,
  ScrollView,
} from 'react-native';
import * as Device from 'expo-device';
import { useAppStore } from '../stores/appStore';

/**
 * LoginScreen Component
 *
 * Renders the login form
 */
export default function LoginScreen() {
  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Get the login function and error from the global store
  const { login, error, clearError } = useAppStore();

  /**
   * Handle Login Button Press
   *
   * This function:
   * 1. Validates the form
   * 2. Gets device information
   * 3. Calls the backend login API
   * 4. Shows error if login fails
   */
  const handleLogin = async () => {
    // Validation: Check if email and password are entered
    if (!email || !password) {
      Alert.alert('Validation Error', 'Please enter both email and password');
      return;
    }

    // Validation: Check if email looks valid
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      Alert.alert('Validation Error', 'Please enter a valid email address');
      return;
    }

    try {
      setIsLoading(true);

      // Get device information for device fingerprinting
      // This prevents token sharing between devices
      const deviceId = `${Platform.OS}_${Device.modelId || 'unknown'}`;
      const deviceName = Device.deviceName || 'Unknown Device';
      const deviceOs = Platform.OS === 'ios' ? 'iOS' : 'Android';

      console.log('[LoginScreen] Logging in...', {
        email,
        deviceId,
        deviceOs,
      });

      // Call the login function from the store
      // This will:
      // 1. Send credentials to backend
      // 2. Receive access and refresh tokens
      // 3. Update the global auth state
      // 4. Automatically show HomeScreen (because auth.isAuthenticated becomes true)
      await login(email, password, deviceId, deviceName, deviceOs);

      console.log('[LoginScreen] Login successful!');
    } catch (err: any) {
      console.error('[LoginScreen] Login failed:', err);

      // Show error message from API or generic error
      const errorMessage =
        err.response?.data?.message || 'Login failed. Please try again.';
      Alert.alert('Login Failed', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.content}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Accountancy</Text>
            <Text style={styles.subtitle}>Mobile App</Text>
          </View>

          {/* Error Alert */}
          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{error.message}</Text>
              <TouchableOpacity onPress={clearError} style={styles.errorDismiss}>
                <Text style={styles.errorDismissText}>×</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Email Input */}
          <View style={styles.formGroup}>
            <Text style={styles.label}>Email Address</Text>
            <TextInput
              style={styles.input}
              placeholder="user@example.com"
              placeholderTextColor="#999"
              value={email}
              onChangeText={setEmail}
              editable={!isLoading}
              autoCapitalize="none"
              autoComplete="email"
              keyboardType="email-address"
              textContentType="emailAddress"
            />
          </View>

          {/* Password Input */}
          <View style={styles.formGroup}>
            <Text style={styles.label}>Password</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter your password"
              placeholderTextColor="#999"
              value={password}
              onChangeText={setPassword}
              editable={!isLoading}
              secureTextEntry
              textContentType="password"
            />
          </View>

          {/* Login Button */}
          <TouchableOpacity
            style={[
              styles.loginButton,
              isLoading && styles.loginButtonDisabled,
            ]}
            onPress={handleLogin}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.loginButtonText}>Login</Text>
            )}
          </TouchableOpacity>

          {/* Info Text */}
          <View style={styles.infoContainer}>
            <Text style={styles.infoText}>
              Demo: Use any email and password to test
            </Text>
            <Text style={styles.infoText}>
              The app will connect to your local backend
            </Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

/**
 * Styles for the Login Screen
 *
 * Colors used:
 * - #007AFF: Apple blue (standard iOS color)
 * - #f0f0f0: Light gray background
 * - #333: Dark text
 * - #ff3b30: Red for errors
 */
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },

  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingVertical: 40,
  },

  content: {
    width: '100%',
  },

  // ============= HEADER =============
  header: {
    marginBottom: 40,
    alignItems: 'center',
  },

  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },

  subtitle: {
    fontSize: 16,
    color: '#999',
  },

  // ============= ERROR =============
  errorContainer: {
    backgroundColor: '#ffe0e0',
    borderColor: '#ff3b30',
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  errorText: {
    color: '#ff3b30',
    fontSize: 14,
    flex: 1,
  },

  errorDismiss: {
    padding: 4,
  },

  errorDismissText: {
    fontSize: 24,
    color: '#ff3b30',
    fontWeight: 'bold',
  },

  // ============= FORM =============
  formGroup: {
    marginBottom: 20,
  },

  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },

  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 16,
    backgroundColor: '#f9f9f9',
  },

  // ============= BUTTON =============
  loginButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 10,
  },

  loginButtonDisabled: {
    opacity: 0.6,
  },

  loginButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },

  // ============= INFO =============
  infoContainer: {
    marginTop: 30,
    padding: 12,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
  },

  infoText: {
    fontSize: 12,
    color: '#666',
    marginBottom: 6,
  },
});
