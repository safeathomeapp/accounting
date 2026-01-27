import { useState, useEffect, useCallback } from 'react'
import { useAuthStore } from '../stores/authStore'
import { dataQualityAPI } from '../services/api'

function CoverageBar({ label, pct }) {
  const color = pct >= 90 ? 'bg-green-500' : pct >= 70 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium text-gray-700 dark:text-gray-300">{label}</span>
        <span className="text-gray-500 dark:text-gray-400">{pct}%</span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
        <div className={`${color} h-2.5 rounded-full transition-all`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
    </div>
  )
}

function Section({ title, children, action }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h2>
        {action}
      </div>
      {children}
    </div>
  )
}

export default function DataQuality() {
  const { user } = useAuthStore()
  const orgId = user?.organization_id

  const [coverage, setCoverage] = useState(null)
  const [quarantine, setQuarantine] = useState([])
  const [unmapped, setUnmapped] = useState([])
  const [mappings, setMappings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionMsg, setActionMsg] = useState(null)

  // New mapping form
  const [showAddForm, setShowAddForm] = useState(false)
  const [newMapping, setNewMapping] = useState({
    platform_name: '',
    source_type: '',
    source_status: '',
    normalized_type: 'SALES_INVOICE',
    normalized_status: 'APPROVED',
    canonical_bucket: 'AR_CURRENT',
    effective_date_source: 'TRANSACTION_DATE',
  })

  const loadData = useCallback(async () => {
    if (!orgId) return
    setLoading(true)
    setError(null)
    try {
      const [covRes, qRes, umRes, mRes] = await Promise.all([
        dataQualityAPI.getCoverage(orgId),
        dataQualityAPI.getQuarantine(orgId),
        dataQualityAPI.getUnmappedTypes(orgId),
        dataQualityAPI.listMappings(),
      ])
      setCoverage(covRes.data)
      setQuarantine(qRes.data.entries || [])
      setUnmapped(umRes.data.unmapped_types || [])
      setMappings(mRes.data.mappings || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data quality information')
    } finally {
      setLoading(false)
    }
  }, [orgId])

  useEffect(() => { loadData() }, [loadData])

  const handleResolve = async (quarantineId) => {
    try {
      const res = await dataQualityAPI.resolveQuarantine(orgId, quarantineId)
      setActionMsg(res.data.resolved ? 'Resolved successfully' : 'Could not resolve - no matching mapping')
      loadData()
    } catch { setActionMsg('Failed to resolve') }
  }

  const handleResolveAll = async () => {
    try {
      const res = await dataQualityAPI.resolveAllQuarantine(orgId)
      setActionMsg(`Resolved: ${res.data.resolved}, Still quarantined: ${res.data.still_quarantined}`)
      loadData()
    } catch { setActionMsg('Failed to resolve all') }
  }

  const handleRebuild = async () => {
    if (!confirm('This will delete and rebuild all canonical facts. Continue?')) return
    try {
      const res = await dataQualityAPI.rebuildFacts(orgId)
      setActionMsg(`Rebuilt: ${res.data.mapped} mapped, ${res.data.quarantined} quarantined`)
      loadData()
    } catch { setActionMsg('Failed to rebuild facts') }
  }

  const handleAddMapping = async (e) => {
    e.preventDefault()
    try {
      await dataQualityAPI.createMapping(newMapping)
      setActionMsg('Mapping created successfully')
      setShowAddForm(false)
      setNewMapping({
        platform_name: '', source_type: '', source_status: '',
        normalized_type: 'SALES_INVOICE', normalized_status: 'APPROVED',
        canonical_bucket: 'AR_CURRENT', effective_date_source: 'TRANSACTION_DATE',
      })
      loadData()
    } catch (err) {
      setActionMsg(err.response?.data?.detail || 'Failed to create mapping')
    }
  }

  const handleDeleteMapping = async (id) => {
    if (!confirm('Deactivate this mapping?')) return
    try {
      await dataQualityAPI.deleteMapping(id)
      setActionMsg('Mapping deactivated')
      loadData()
    } catch { setActionMsg('Failed to deactivate mapping') }
  }

  const handlePrefillMapping = (item) => {
    setNewMapping((prev) => ({
      ...prev,
      platform_name: item.platform_name,
      source_type: item.source_type,
      source_status: item.source_status,
    }))
    setShowAddForm(true)
  }

  if (!orgId) {
    return (
      <div className="p-6">
        <p className="text-gray-500 dark:text-gray-400">No organization selected. Please select an organization first.</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-gray-500 dark:text-gray-400">Loading data quality information...</div>
      </div>
    )
  }

  const normalizedTypes = ['SALES_INVOICE', 'PURCHASE_INVOICE', 'CREDIT_NOTE', 'BANK_PAYMENT', 'BANK_RECEIPT', 'JOURNAL', 'TRANSFER', 'OTHER']
  const normalizedStatuses = ['DRAFT', 'AWAITING_APPROVAL', 'APPROVED', 'SENT', 'PAID', 'VOIDED', 'UNKNOWN']
  const buckets = ['AR_CURRENT', 'AR_OVERDUE', 'AP_CURRENT', 'AP_OVERDUE', 'CASH_IN', 'CASH_OUT', 'NON_CASH', 'IGNORE']
  const dateSources = ['TRANSACTION_DATE', 'DUE_DATE']

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Data Quality Dashboard</h1>
          <button
            onClick={handleRebuild}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm"
          >
            Rebuild All Facts
          </button>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 p-4 rounded-lg mb-6">
            {error}
          </div>
        )}

        {actionMsg && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-400 p-4 rounded-lg mb-6 flex justify-between items-center">
            <span>{actionMsg}</span>
            <button onClick={() => setActionMsg(null)} className="text-blue-500 hover:text-blue-700 ml-4">Dismiss</button>
          </div>
        )}

        {/* Coverage Summary */}
        <Section title="Mapping Coverage">
          {coverage?.overall && (
            <div className="mb-4">
              <CoverageBar label="Overall" pct={coverage.overall.coverage_pct} />
              <div className="grid grid-cols-4 gap-4 mt-4 text-center">
                <div className="bg-gray-50 dark:bg-gray-700 rounded p-3">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">{coverage.overall.total_transactions}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Total</div>
                </div>
                <div className="bg-green-50 dark:bg-green-900/20 rounded p-3">
                  <div className="text-2xl font-bold text-green-600">{coverage.overall.mapped_count}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Mapped</div>
                </div>
                <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded p-3">
                  <div className="text-2xl font-bold text-yellow-600">{coverage.overall.quarantined_count}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Quarantined</div>
                </div>
                <div className="bg-red-50 dark:bg-red-900/20 rounded p-3">
                  <div className="text-2xl font-bold text-red-600">{coverage.overall.unmapped_count}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Unmapped</div>
                </div>
              </div>
            </div>
          )}
          {coverage?.by_platform?.length > 0 && (
            <div className="mt-4 pt-4 border-t dark:border-gray-700">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">By Platform</h3>
              {coverage.by_platform.map((p) => (
                <CoverageBar key={p.platform_name} label={p.platform_name} pct={p.coverage_pct} />
              ))}
            </div>
          )}
        </Section>

        {/* Quarantine Queue */}
        <Section
          title={`Quarantine Queue (${quarantine.length})`}
          action={
            quarantine.length > 0 && (
              <button onClick={handleResolveAll} className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700">
                Resolve All
              </button>
            )
          }
        >
          {quarantine.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-sm">No quarantined transactions.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 dark:text-gray-400 border-b dark:border-gray-700">
                    <th className="pb-2 pr-4">Platform</th>
                    <th className="pb-2 pr-4">Type</th>
                    <th className="pb-2 pr-4">Status</th>
                    <th className="pb-2 pr-4">Reason</th>
                    <th className="pb-2 pr-4">Date</th>
                    <th className="pb-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {quarantine.map((e) => (
                    <tr key={e.id} className="border-b dark:border-gray-700">
                      <td className="py-2 pr-4 text-gray-700 dark:text-gray-300">{e.platform_name}</td>
                      <td className="py-2 pr-4 text-gray-700 dark:text-gray-300">{e.source_type}</td>
                      <td className="py-2 pr-4 text-gray-700 dark:text-gray-300">{e.source_status}</td>
                      <td className="py-2 pr-4 text-gray-500 dark:text-gray-400 max-w-xs truncate">{e.reason}</td>
                      <td className="py-2 pr-4 text-gray-500 dark:text-gray-400">
                        {e.quarantined_at ? new Date(e.quarantined_at).toLocaleDateString() : '-'}
                      </td>
                      <td className="py-2">
                        <button onClick={() => handleResolve(e.id)} className="text-blue-600 hover:text-blue-800 text-xs">
                          Resolve
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        {/* Unmapped Types */}
        <Section
          title={`Unmapped Types (${unmapped.length})`}
          action={
            <button onClick={() => setShowAddForm(!showAddForm)} className="px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700">
              {showAddForm ? 'Cancel' : 'Add Mapping'}
            </button>
          }
        >
          {showAddForm && (
            <form onSubmit={handleAddMapping} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Platform</label>
                  <input type="text" required value={newMapping.platform_name} onChange={(e) => setNewMapping({ ...newMapping, platform_name: e.target.value })}
                    className="w-full px-2 py-1 border dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white" placeholder="xero" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Source Type</label>
                  <input type="text" required value={newMapping.source_type} onChange={(e) => setNewMapping({ ...newMapping, source_type: e.target.value })}
                    className="w-full px-2 py-1 border dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white" placeholder="invoice" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Source Status</label>
                  <input type="text" required value={newMapping.source_status} onChange={(e) => setNewMapping({ ...newMapping, source_status: e.target.value })}
                    className="w-full px-2 py-1 border dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white" placeholder="approved" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Normalized Type</label>
                  <select value={newMapping.normalized_type} onChange={(e) => setNewMapping({ ...newMapping, normalized_type: e.target.value })}
                    className="w-full px-2 py-1 border dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
                    {normalizedTypes.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Normalized Status</label>
                  <select value={newMapping.normalized_status} onChange={(e) => setNewMapping({ ...newMapping, normalized_status: e.target.value })}
                    className="w-full px-2 py-1 border dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
                    {normalizedStatuses.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Bucket</label>
                  <select value={newMapping.canonical_bucket} onChange={(e) => setNewMapping({ ...newMapping, canonical_bucket: e.target.value })}
                    className="w-full px-2 py-1 border dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
                    {buckets.map((b) => <option key={b} value={b}>{b}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Date Source</label>
                  <select value={newMapping.effective_date_source} onChange={(e) => setNewMapping({ ...newMapping, effective_date_source: e.target.value })}
                    className="w-full px-2 py-1 border dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
                    {dateSources.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>
              </div>
              <button type="submit" className="px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700">
                Create Mapping
              </button>
            </form>
          )}

          {unmapped.length === 0 ? (
            <p className="text-green-600 dark:text-green-400 text-sm">All transaction types are mapped.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 dark:text-gray-400 border-b dark:border-gray-700">
                    <th className="pb-2 pr-4">Platform</th>
                    <th className="pb-2 pr-4">Type</th>
                    <th className="pb-2 pr-4">Status</th>
                    <th className="pb-2 pr-4">Count</th>
                    <th className="pb-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {unmapped.map((u, i) => (
                    <tr key={i} className="border-b dark:border-gray-700">
                      <td className="py-2 pr-4 text-gray-700 dark:text-gray-300">{u.platform_name}</td>
                      <td className="py-2 pr-4 text-gray-700 dark:text-gray-300">{u.source_type}</td>
                      <td className="py-2 pr-4 text-gray-700 dark:text-gray-300">{u.source_status}</td>
                      <td className="py-2 pr-4 text-gray-500 dark:text-gray-400">{u.transaction_count}</td>
                      <td className="py-2">
                        <button onClick={() => handlePrefillMapping(u)} className="text-indigo-600 hover:text-indigo-800 text-xs">
                          Add Mapping
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        {/* Mapping Management */}
        <Section title={`Active Mappings (${mappings.length})`}>
          {mappings.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-sm">No mappings configured yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 dark:text-gray-400 border-b dark:border-gray-700">
                    <th className="pb-2 pr-3">Platform</th>
                    <th className="pb-2 pr-3">Type</th>
                    <th className="pb-2 pr-3">Status</th>
                    <th className="pb-2 pr-3">Normalized Type</th>
                    <th className="pb-2 pr-3">Norm. Status</th>
                    <th className="pb-2 pr-3">Bucket</th>
                    <th className="pb-2 pr-3">Date Source</th>
                    <th className="pb-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {mappings.map((m) => (
                    <tr key={m.id} className="border-b dark:border-gray-700">
                      <td className="py-2 pr-3 text-gray-700 dark:text-gray-300">{m.platform_name}</td>
                      <td className="py-2 pr-3 text-gray-700 dark:text-gray-300">{m.source_type}</td>
                      <td className="py-2 pr-3 text-gray-700 dark:text-gray-300">{m.source_status}</td>
                      <td className="py-2 pr-3 text-gray-500 dark:text-gray-400">{m.normalized_type}</td>
                      <td className="py-2 pr-3 text-gray-500 dark:text-gray-400">{m.normalized_status}</td>
                      <td className="py-2 pr-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          m.canonical_bucket.startsWith('AR') ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                          m.canonical_bucket.startsWith('AP') ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                          m.canonical_bucket.startsWith('CASH') ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                          'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                        }`}>
                          {m.canonical_bucket}
                        </span>
                      </td>
                      <td className="py-2 pr-3 text-gray-500 dark:text-gray-400 text-xs">{m.effective_date_source}</td>
                      <td className="py-2">
                        <button onClick={() => handleDeleteMapping(m.id)} className="text-red-600 hover:text-red-800 text-xs">
                          Deactivate
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>
      </div>
    </div>
  )
}
