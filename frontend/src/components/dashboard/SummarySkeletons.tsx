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

export function MealsSectionSkeleton() {
  return (
    <div className="bg-card border border-border rounded-xl">
      <div className="px-4 py-3 border-b border-border flex justify-between">
        <div className="h-4 w-20 bg-border rounded animate-pulse" />
        <div className="h-6 w-20 bg-border rounded animate-pulse" />
      </div>
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="border-b border-border last:border-0 px-3 py-3 space-y-2">
          <div className="flex justify-between items-center">
            <div className="h-4 w-24 bg-border rounded animate-pulse" />
            <div className="h-4 w-12 bg-border rounded animate-pulse" />
          </div>
          <div className="h-3 w-32 bg-border rounded animate-pulse" />
        </div>
      ))}
    </div>
  )
}

export function WeeklyChartsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-[3fr_2fr] gap-4">
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="h-4 w-32 bg-border rounded animate-pulse mb-4" />
        <div className="h-60 bg-border rounded animate-pulse" />
      </div>
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="h-4 w-32 bg-border rounded animate-pulse mb-4" />
        <div className="space-y-2">
          {[1, 2, 3, 4, 5, 6, 7].map((i) => (
            <div key={i} className="flex gap-2 items-center">
              <div className="h-3 w-12 bg-border rounded animate-pulse" />
              <div className="h-2 flex-1 bg-border rounded animate-pulse" />
              <div className="h-3 w-16 bg-border rounded animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
