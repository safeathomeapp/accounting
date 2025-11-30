import { useState } from 'react'

export function useBulkSelection(items = []) {
  const [selected, setSelected] = useState(new Set())

  const toggleItem = (id) => {
    const newSelected = new Set(selected)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelected(newSelected)
  }

  const selectAll = () => {
    setSelected(new Set(items.map((item) => item.id)))
  }

  const deselectAll = () => {
    setSelected(new Set())
  }

  const getSelectedItems = () => {
    return items.filter((item) => selected.has(item.id))
  }

  const isItemSelected = (id) => selected.has(id)

  const isAllSelected = items.length > 0 && selected.size === items.length

  const hasSelection = selected.size > 0

  return {
    selected,
    toggleItem,
    selectAll,
    deselectAll,
    getSelectedItems,
    isItemSelected,
    isAllSelected,
    hasSelection,
    count: selected.size,
  }
}
