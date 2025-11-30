export function exportToCSV(data, filename, columns) {
  if (!data || data.length === 0) {
    console.warn('No data to export')
    return
  }

  // Build CSV header
  const headers = columns.map((col) => `"${col.label}"`).join(',')

  // Build CSV rows
  const rows = data.map((row) =>
    columns
      .map((col) => {
        let value = row[col.key]
        if (value === null || value === undefined) return '""'
        if (typeof value === 'string') return `"${value.replace(/"/g, '""')}"`
        if (typeof value === 'object') return `"${JSON.stringify(value)}"`
        return `"${value}"`
      })
      .join(',')
  )

  // Combine header + rows
  const csv = [headers, ...rows].join('\n')

  // Download
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${filename}-${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}
