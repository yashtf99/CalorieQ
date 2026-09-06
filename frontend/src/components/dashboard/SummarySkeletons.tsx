export function CalorieRingSkeleton() {
  const size = (72 + 10) * 2 + 4
  return (
    <div className="flex flex-col items-center gap-4 py-2">
      <div
        className="rounded-full bg-border animate-pulse"
        style={{ width: size, height: size }}
      />
      <div className="h-4 w-32 rounded bg-border animate-pulse" />
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
