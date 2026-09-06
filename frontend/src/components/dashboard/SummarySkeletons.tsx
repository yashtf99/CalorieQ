export function CalorieRingSkeleton() {
  const size = (46 + 7) * 2 + 4
  return (
    <div className="flex items-center gap-5 pl-2 pr-5 py-3">
      <div
        className="rounded-full bg-border animate-pulse flex-shrink-0"
        style={{ width: size, height: size }}
      />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-24 rounded bg-border animate-pulse" />
        <div className="h-6 w-32 rounded bg-border animate-pulse" />
        <div className="h-3 w-40 rounded bg-border animate-pulse" />
      </div>
    </div>
  )
}

export function MacroCardSkeleton() {
  return (
    <div className="bg-card border border-border rounded-xl p-5 space-y-4">
      <div className="h-4 w-32 rounded bg-border animate-pulse" />
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="space-y-2">
          <div className="flex justify-between">
            <div className="h-3 w-16 rounded bg-border animate-pulse" />
            <div className="h-3 w-20 rounded bg-border animate-pulse" />
          </div>
          <div className="h-2 rounded-full bg-border animate-pulse" />
        </div>
      ))}
    </div>
  )
}
