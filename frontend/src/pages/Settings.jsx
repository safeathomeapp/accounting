/**
 * Settings Page
 *
 * Company settings with user management and access levels.
 * Features:
 * - User management (add/remove users)
 * - Access level settings (role-based)
 * - Company profile
 * - Integration settings
 *
 * @author Claude Code
 * @created January 25, 2026
 * @updated January 26, 2026 - Added user management functionality
 */

import { useState, useEffect } from 'react'
import Navigation from '../components/Navigation'
import { usersAPI } from '../services/api'
import { useToastStore } from '../stores/toastStore'

// Role badge colors
const ROLE_COLORS = {
  admin: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  manager: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  accountant: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  viewer: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState('users')
  const [users, setUsers] = useState([])
  const [roles, setRoles] = useState([])
  const [loading, setLoading] = useState(true)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [showRoleModal, setShowRoleModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [inviteForm, setInviteForm] = useState({ email: '', name: '', role: 'viewer' })
  const [inviteResult, setInviteResult] = useState(null)
  const addToast = useToastStore((state) => state.addToast)

  // Get current user from localStorage
  const currentUser = JSON.parse(localStorage.getItem('authUser') || '{}')
  const isAdmin = currentUser.is_admin || currentUser.role === 'admin'

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [usersRes, rolesRes] = await Promise.all([
        usersAPI.list(),
        usersAPI.getRoles(),
      ])
      setUsers(usersRes.data.users || [])
      setRoles(rolesRes.data.roles || [])
    } catch (error) {
      console.error('Failed to load data:', error)
      addToast('Failed to load user data', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleInviteUser = async (e) => {
    e.preventDefault()
    try {
      const response = await usersAPI.invite(inviteForm)
      setInviteResult(response.data)
      addToast('User invited successfully', 'success')
      loadData()
    } catch (error) {
      addToast(error.response?.data?.detail || 'Failed to invite user', 'error')
    }
  }

  const handleUpdateRole = async (newRole) => {
    if (!selectedUser) return
    try {
      await usersAPI.updateRole(selectedUser.id, newRole)
      addToast(`Role updated to ${newRole}`, 'success')
      setShowRoleModal(false)
      setSelectedUser(null)
      loadData()
    } catch (error) {
      addToast(error.response?.data?.detail || 'Failed to update role', 'error')
    }
  }

  const handleRemoveUser = async (user) => {
    if (!confirm(`Are you sure you want to remove ${user.name}?`)) return
    try {
      await usersAPI.remove(user.id)
      addToast('User removed successfully', 'success')
      loadData()
    } catch (error) {
      addToast(error.response?.data?.detail || 'Failed to remove user', 'error')
    }
  }

  const closeInviteModal = () => {
    setShowInviteModal(false)
    setInviteForm({ email: '', name: '', role: 'viewer' })
    setInviteResult(null)
  }

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

      {/* Tab Navigation */}
      <div className="max-w-7xl mx-auto px-4 pt-6">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('users')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'users'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400'
              }`}
            >
              User Management
            </button>
            <button
              onClick={() => setActiveTab('roles')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'roles'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400'
              }`}
            >
              Access Levels
            </button>
            <button
              onClick={() => setActiveTab('company')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'company'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400'
              }`}
            >
              Company Profile
            </button>
            <button
              onClick={() => setActiveTab('integrations')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'integrations'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400'
              }`}
            >
              Integrations
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* User Management Tab */}
        {activeTab === 'users' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Team Members
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {users.length} user{users.length !== 1 ? 's' : ''} in your organization
                </p>
              </div>
              {isAdmin && (
                <button
                  onClick={() => setShowInviteModal(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Invite User
                </button>
              )}
            </div>

            {/* User List */}
            {loading ? (
              <div className="p-8 text-center text-gray-500">Loading users...</div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {users.map((user) => (
                  <div key={user.id} className="px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {/* Avatar */}
                      <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
                        {user.name.charAt(0).toUpperCase()}
                      </div>
                      {/* Info */}
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {user.name}
                          {user.id === currentUser.id && (
                            <span className="ml-2 text-xs text-gray-500">(you)</span>
                          )}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{user.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {/* Role Badge */}
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${ROLE_COLORS[user.role] || ROLE_COLORS.viewer}`}>
                        {user.role?.charAt(0).toUpperCase() + user.role?.slice(1) || 'Viewer'}
                      </span>
                      {/* Last Login */}
                      <span className="text-sm text-gray-500 dark:text-gray-400 hidden sm:block">
                        {user.last_login
                          ? `Last login: ${new Date(user.last_login).toLocaleDateString()}`
                          : 'Never logged in'}
                      </span>
                      {/* Actions */}
                      {isAdmin && user.id !== currentUser.id && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              setSelectedUser(user)
                              setShowRoleModal(true)
                            }}
                            className="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                            title="Change role"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                          <button
                            onClick={() => handleRemoveUser(user)}
                            className="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                            title="Remove user"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {users.length === 0 && (
                  <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                    No users found. Invite team members to get started.
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Access Levels Tab */}
        {activeTab === 'roles' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Access Levels
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Configure role-based permissions for your team
              </p>
            </div>
            <div className="p-6 grid gap-4">
              {roles.map((role) => (
                <div
                  key={role.id}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${ROLE_COLORS[role.id]}`}>
                        {role.name}
                      </span>
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {users.filter((u) => u.role === role.id).length} user(s)
                      </span>
                    </div>
                  </div>
                  <p className="mt-2 text-gray-600 dark:text-gray-400">
                    {role.description}
                  </p>
                  {/* Permissions list */}
                  <div className="mt-3 flex flex-wrap gap-2">
                    {role.id === 'admin' && (
                      <>
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">Manage Users</span>
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">Manage Settings</span>
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">View Reports</span>
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">Edit Transactions</span>
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">Manage Clients</span>
                      </>
                    )}
                    {role.id === 'manager' && (
                      <>
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">View Reports</span>
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">Edit Transactions</span>
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">Manage Clients</span>
                      </>
                    )}
                    {role.id === 'accountant' && (
                      <>
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">View Reports</span>
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">Edit Transactions</span>
                      </>
                    )}
                    {role.id === 'viewer' && (
                      <>
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">View Only</span>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Company Profile Tab */}
        {activeTab === 'company' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Company Profile
            </h2>
            <p className="text-gray-500 dark:text-gray-400">
              Company profile settings coming soon.
            </p>
          </div>
        )}

        {/* Integrations Tab */}
        {activeTab === 'integrations' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Platform Integrations
            </h2>
            <div className="grid gap-4">
              <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                    <span className="text-blue-600 dark:text-blue-400 font-bold">X</span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Xero</p>
                    <p className="text-sm text-gray-500">Accounting platform</p>
                  </div>
                </div>
                <span className="px-3 py-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300 rounded-full text-sm">
                  Available
                </span>
              </div>
              <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                    <span className="text-green-600 dark:text-green-400 font-bold">QB</span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">QuickBooks</p>
                    <p className="text-sm text-gray-500">Accounting platform</p>
                  </div>
                </div>
                <span className="px-3 py-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300 rounded-full text-sm">
                  Available
                </span>
              </div>
              <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
                    <span className="text-purple-600 dark:text-purple-400 font-bold">FA</span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">FreeAgent</p>
                    <p className="text-sm text-gray-500">Accounting platform</p>
                  </div>
                </div>
                <span className="px-3 py-1 bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300 rounded-full text-sm">
                  Coming Soon
                </span>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Invite User Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Invite New User
              </h3>
              <button
                onClick={closeInviteModal}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <form onSubmit={handleInviteUser} className="p-6">
              {inviteResult ? (
                <div className="text-center">
                  <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    User Invited!
                  </h4>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">
                    {inviteResult.user?.name} has been added to your organization.
                  </p>
                  <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4 text-left">
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Temporary Password:</p>
                    <p className="font-mono text-lg text-gray-900 dark:text-white">
                      {inviteResult.temp_password}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      Share this password securely with the user. They should change it on first login.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={closeInviteModal}
                    className="mt-6 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Done
                  </button>
                </div>
              ) : (
                <>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Full Name
                      </label>
                      <input
                        type="text"
                        value={inviteForm.name}
                        onChange={(e) => setInviteForm({ ...inviteForm, name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        placeholder="John Smith"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Email Address
                      </label>
                      <input
                        type="email"
                        value={inviteForm.email}
                        onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        placeholder="john@company.com"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Role
                      </label>
                      <select
                        value={inviteForm.role}
                        onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      >
                        {roles.map((role) => (
                          <option key={role.id} value={role.id}>
                            {role.name} - {role.description}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="mt-6 flex gap-3">
                    <button
                      type="button"
                      onClick={closeInviteModal}
                      className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Send Invite
                    </button>
                  </div>
                </>
              )}
            </form>
          </div>
        </div>
      )}

      {/* Change Role Modal */}
      {showRoleModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Change Role
              </h3>
              <button
                onClick={() => {
                  setShowRoleModal(false)
                  setSelectedUser(null)
                }}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6">
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Select a new role for <strong>{selectedUser.name}</strong>:
              </p>
              <div className="space-y-2">
                {roles.map((role) => (
                  <button
                    key={role.id}
                    onClick={() => handleUpdateRole(role.id)}
                    className={`w-full p-4 text-left border rounded-lg transition-colors ${
                      selectedUser.role === role.id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${ROLE_COLORS[role.id]}`}>
                        {role.name}
                      </span>
                      {selectedUser.role === role.id && (
                        <span className="text-blue-600 dark:text-blue-400 text-sm">Current</span>
                      )}
                    </div>
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                      {role.description}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
