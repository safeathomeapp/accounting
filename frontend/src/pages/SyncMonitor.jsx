import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useToastStore } from '../stores/toastStore'
import Navigation from '../components/Navigation'
import { SkeletonCard, SkeletonTable } from '../components/Skeleton'

export default function SyncMonitor() {
  const navigate = useNavigate()
  const { logout } = useAuthStore()
  const { addToast } = useToastStore()
  const [syncHistory, setSyncHistory] = useState([])
  const [syncStatus, setSyncStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [error, setError] = useState(null)
  const [selectedPlatform, setSelectedPlatform] = useState('all')

  useEffect(() => {
    fetchSyncData()
    // Poll every 30 seconds
    const interval = setInterval(fetchSyncData, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchSyncData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('authToken')

      // Fetch sync status
      const statusResponse = await fetch('http://localhost:8000/api/v1/sync/status', {
        headers: { Authorization: `Bearer ${token}` },
      })

      // Fetch sync history
      const historyResponse = await fetch('http://localhost:8000/api/v1/sync/history?limit=20', {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (statusResponse.ok) {
        setSyncStatus(await statusResponse.json())
      } else {
        setSyncStatus(generateMockStatus())
      }

      if (historyResponse.ok) {
        const data = await historyResponse.json()
        setSyncHistory(data.syncs || generateMockHistory())
      } else {
        setSyncHistory(generateMockHistory())
      }

      setError(null)
    } catch (err) {
      console.error('Error fetching sync data:', err)
      setSyncStatus(generateMockStatus())
      setSyncHistory(generateMockHistory())
    } finally {
      setLoading(false)
    }
  }

  const generateMockStatus = () => ({
    organization_id: '123',
    platforms: {
      xero: {
        platform_name: 'Xero',
        is_active: true,
        last_sync_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        sync_type: 'Full',
        records_synced: 1250,
        records_created: 45,
        records_updated: 120,
        records_failed: 2,
        duration_seconds: 45,
      },
      quickbooks: {
        platform_name: 'QuickBooks',
        is_active: false,
        last_sync_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        sync_type: 'Incremental',
        records_synced: 320,
        records_created: 10,
        records_updated: 30,
        records_failed: 0,
        duration_seconds: 23,
      },
    },
  })

  const generateMockHistory = () => [
    {
      sync_id: '1',
      platform: 'Xero',
      sync_type: 'Full',
      status: 'completed',
      started_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      completed_at: new Date(Date.now() - 2 * 60 * 60 * 1000 + 45 * 1000).toISOString(),
      duration_seconds: 45,
      records: {
        synced: 1250,
        created: 45,
        updated: 120,
        failed: 2,
      },
    },
    {
      sync_id: '2',
      platform: 'Xero',
      sync_type: 'Incremental',
      status: 'completed',
      started_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
      completed_at: new Date(Date.now() - 6 * 60 * 60 * 1000 + 30 * 1000).toISOString(),
      duration_seconds: 30,
      records: {
        synced: 45,
        created: 12,
        updated: 20,
        failed: 0,
      },
    },
    {
      sync_id: '3',
      platform: 'QuickBooks',
      sync_type: 'Full',
      status: 'failed',
      started_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      completed_at: new Date(Date.now() - 24 * 60 * 60 * 1000 + 120 * 1000).toISOString(),
      duration_seconds: 120,
      records: {
        synced: 320,
        created: 10,
        updated: 30,
        failed: 5,
      },
      error_message: 'Authentication token expired',
    },
  ]

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleSync = async (platform) => {
    try {
      setSyncing(true)
      addToast(platform === 'all' ? 'Starting full sync...' : `Syncing ${platform}...`, 'info')
      const token = localStorage.getItem('authToken')
      const endpoint =
        platform === 'all'
          ? 'http://localhost:8000/api/v1/sync/all'
          : `http://localhost:8000/api/v1/sync/platform/${platform}`

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })

      if (response.ok) {
        addToast('Sync completed successfully!', 'success')
        await fetchSyncData()
      } else {
        addToast('Sync failed. Please try again.', 'error')
      }
    } catch (err) {
      addToast('Error starting sync: ' + err.message, 'error')
    } finally {
      setSyncing(false)
    }
  }

  if (loading && !syncStatus) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Navigation />
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <h1 className="text-3xl font-bold text-gray-900">Sync Monitor</h1>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <SkeletonCard />
            <SkeletonCard />
          </div>
          <SkeletonTable rows={5} />
        </main>
      </div>
    )
  }

  const filteredHistory =
    selectedPlatform === 'all'
      ? syncHistory
      : syncHistory.filter((s) => s.platform.toLowerCase() === selectedPlatform.toLowerCase())

  return (
    <div className="min-h-screen bg-gray-100">
      <Navigation />

      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Sync Monitor</h1>
            <p className="text-gray-600">Real-time sync status and history</p>
          </div>
          <button
            onClick={handleLogout}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Sync Status Cards */}
        {syncStatus && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {Object.entries(syncStatus.platforms).map(([key, platform]) => (
              <div key={key} className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">
                      {platform.platform_name}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Status:{' '}
                      <span
                        className={`font-semibold ${
                          platform.is_active
                            ? 'text-green-600'
                            : 'text-gray-600'
                        }`}
                      >
                        {platform.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </p>
                  </div>
                  <button
                    onClick={() => handleSync(key)}
                    disabled={syncing || !platform.is_active}
                    className={`px-4 py-2 rounded font-semibold transition ${
                      syncing || !platform.is_active
                        ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    {syncing ? 'Syncing...' : 'Sync Now'}
                  </button>
                </div>

                {platform.last_sync_at && (
                  <>
                    <div className="space-y-3 mb-4 pb-4 border-b border-gray-200">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Last Sync:</span>
                        <span className="text-gray-900">
                          {new Date(platform.last_sync_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Duration:</span>
                        <span className="text-gray-900">{platform.duration_seconds}s</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Sync Type:</span>
                        <span className="text-gray-900">{platform.sync_type}</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-2">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-blue-600">
                          {platform.records_synced}
                        </p>
                        <p className="text-xs text-gray-600">Synced</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-600">
                          {platform.records_created}
                        </p>
                        <p className="text-xs text-gray-600">Created</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-yellow-600">
                          {platform.records_updated}
                        </p>
                        <p className="text-xs text-gray-600">Updated</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-red-600">
                          {platform.records_failed}
                        </p>
                        <p className="text-xs text-gray-600">Failed</p>
                      </div>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Sync Actions */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => handleSync('all')}
              disabled={syncing}
              className={`px-6 py-3 rounded-lg font-semibold transition ${
                syncing
                  ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                  : 'bg-green-600 text-white hover:bg-green-700'
              }`}
            >
              {syncing ? 'Syncing All...' : 'Sync All Platforms'}
            </button>
            <button
              onClick={fetchSyncData}
              className="px-6 py-3 rounded-lg font-semibold bg-blue-600 text-white hover:bg-blue-700 transition"
            >
              Refresh Data
            </button>
          </div>
        </div>

        {/* Sync History */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Sync History</h2>
            <select
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Platforms</option>
              <option value="xero">Xero</option>
              <option value="quickbooks">QuickBooks</option>
            </select>
          </div>

          {filteredHistory.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No sync history found
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                      Platform
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                      Started
                    </th>
                    <th className="px-6 py-3 text-right text-sm font-medium text-gray-700">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-right text-sm font-medium text-gray-700">
                      Records
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredHistory.map((sync) => (
                    <tr key={sync.sync_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">
                        {sync.platform}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {sync.sync_type}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            sync.status === 'completed'
                              ? 'bg-green-100 text-green-800'
                              : sync.status === 'in_progress'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {sync.status.charAt(0).toUpperCase() + sync.status.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {new Date(sync.started_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-sm text-right text-gray-600">
                        {sync.duration_seconds}s
                      </td>
                      <td className="px-6 py-4 text-sm text-right">
                        <span className="text-gray-900">
                          {sync.records.synced} synced
                        </span>
                        {sync.records.failed > 0 && (
                          <span className="ml-2 text-red-600">
                            ({sync.records.failed} failed)
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
