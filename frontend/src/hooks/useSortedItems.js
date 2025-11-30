import { useState } from 'react'

export function useSortedItems(items = []) {
  const [sortKey, setSortKey] = useState(null)
  const [sortAsc, setSortAsc] = useState(true)

  const toggleSort = (key) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc)
    } else {
      setSortKey(key)
      setSortAsc(true)
    }
  }

  const getSorted = () => {
    if (!sortKey) return items

    return [...items].sort((a, b) => {
      const aVal = a[sortKey]
      const bVal = b[sortKey]

      if (typeof aVal === 'string') {
        return sortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
      }
      if (typeof aVal === 'number') {
        return sortAsc ? aVal - bVal : bVal - aVal
      }
      if (aVal instanceof Date) {
        return sortAsc ? aVal - bVal : bVal - aVal
      }
      return 0
    })
  }

  const getSortIndicator = (key) => {
    if (sortKey !== key) return ' ⇅'
    return sortAsc ? ' ↑' : ' ↓'
  }

  return {
    sortKey,
    sortAsc,
    toggleSort,
    getSorted,
    getSortIndicator,
  }
}
