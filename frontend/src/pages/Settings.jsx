/**
 * Settings Page
 *
 * Placeholder for company settings, user management, and access levels.
 * Will be expanded to include:
 * - User management (add/remove users)
 * - Access level settings
 * - Company profile
 * - Integration settings
 *
 * @author Claude Code
 * @created January 25, 2026
 */

import Navigation from '../components/Navigation'

export default function Settings() {
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Navigation />

      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your company and user settings
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* User Management Card */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <h3 className="ml-4 text-lg font-semibold text-gray-900 dark:text-white">
                User Management
              </h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Add, remove, and manage user accounts with different access levels.
            </p>
            <span className="inline-block px-3 py-1 bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300 rounded-full text-sm font-medium">
              Coming Soon
            </span>
          </div>

          {/* Access Levels Card */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 className="ml-4 text-lg font-semibold text-gray-900 dark:text-white">
                Access Levels
              </h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Configure role-based permissions and access controls for your team.
            </p>
            <span className="inline-block px-3 py-1 bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300 rounded-full text-sm font-medium">
              Coming Soon
            </span>
          </div>

          {/* Company Profile Card */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <h3 className="ml-4 text-lg font-semibold text-gray-900 dark:text-white">
                Company Profile
              </h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Update your company details, logo, and business information.
            </p>
            <span className="inline-block px-3 py-1 bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300 rounded-full text-sm font-medium">
              Coming Soon
            </span>
          </div>

          {/* Integrations Card */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
                </svg>
              </div>
              <h3 className="ml-4 text-lg font-semibold text-gray-900 dark:text-white">
                Integrations
              </h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Connect with Xero, QuickBooks, and other accounting platforms.
            </p>
            <span className="inline-block px-3 py-1 bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300 rounded-full text-sm font-medium">
              Coming Soon
            </span>
          </div>

          {/* Notifications Card */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-red-100 dark:bg-red-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <h3 className="ml-4 text-lg font-semibold text-gray-900 dark:text-white">
                Notifications
              </h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Configure email alerts, reminders, and notification preferences.
            </p>
            <span className="inline-block px-3 py-1 bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300 rounded-full text-sm font-medium">
              Coming Soon
            </span>
          </div>

          {/* Billing Card */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-yellow-100 dark:bg-yellow-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
              </div>
              <h3 className="ml-4 text-lg font-semibold text-gray-900 dark:text-white">
                Billing & Plans
              </h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Manage your subscription, payment methods, and billing history.
            </p>
            <span className="inline-block px-3 py-1 bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300 rounded-full text-sm font-medium">
              Coming Soon
            </span>
          </div>
        </div>
      </main>
    </div>
  )
}
