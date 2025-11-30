export function SkeletonCard() {
  return (
    <div className="bg-white rounded-lg shadow p-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-24 bg-gray-300 rounded mb-2"></div>
          <div className="h-8 w-16 bg-gray-300 rounded"></div>
        </div>
        <div className="h-12 w-12 bg-gray-300 rounded-lg"></div>
      </div>
    </div>
  )
}

export function SkeletonTable({ rows = 5 }) {
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden animate-pulse">
      <div className="p-6 space-y-4">
        {Array(rows)
          .fill(0)
          .map((_, i) => (
            <div key={i} className="flex gap-4">
              <div className="h-4 flex-1 bg-gray-300 rounded"></div>
              <div className="h-4 w-24 bg-gray-300 rounded"></div>
              <div className="h-4 w-16 bg-gray-300 rounded"></div>
            </div>
          ))}
      </div>
    </div>
  )
}

export function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {Array(4)
        .fill(0)
        .map((_, i) => (
          <SkeletonCard key={i} />
        ))}
    </div>
  )
}
