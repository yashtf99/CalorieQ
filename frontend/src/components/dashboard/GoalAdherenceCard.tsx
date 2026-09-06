import { Check, X } from 'lucide-react'
import type { WeeklyReportOut } from '@/types/reports'

interface Props {
  report: WeeklyReportOut
}

export default function GoalAdherenceCard({ report }: Props) {
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  const adherence = report.data.map((day, i) => {
    if (day.energy_kcal === 0) {
      return { day: days[i], status: 'no_data' as const }
    }
    const isOnTarget = report.goal?.daily_calories
      ? day.energy_kcal <= report.goal.daily_calories
      : true
    return {
      day: days[i],
      status: isOnTarget ? ('on_target' as const) : ('exceeded' as const),
      kcal: day.energy_kcal,
    }
  })

  const onTargetCount = adherence.filter((a) => a.status === 'on_target').length

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold">Goal Adherence</h3>
        <span className="text-xs font-medium text-primary">
          {onTargetCount} / 7 days
        </span>
      </div>

      <div className="space-y-2">
        {adherence.map((a) => (
          <div key={a.day} className="flex items-center gap-3">
            <span className="text-xs font-medium w-8">{a.day}</span>
            <div className="flex-1 h-1.5 rounded-full bg-border overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  a.status === 'on_target'
                    ? 'bg-primary'
                    : a.status === 'exceeded'
                      ? 'bg-destructive'
                      : 'bg-muted'
                }`}
                style={{ width: a.status !== 'no_data' ? '100%' : '0%' }}
              />
            </div>
            <div className="flex items-center gap-2 w-20">
              {a.status === 'on_target' && (
                <>
                  <span className="text-xs font-medium">{a.kcal}</span>
                  <Check className="w-3 h-3 text-primary" />
                </>
              )}
              {a.status === 'exceeded' && (
                <>
                  <span className="text-xs font-medium text-destructive">{a.kcal}</span>
                  <X className="w-3 h-3 text-destructive" />
                </>
              )}
              {a.status === 'no_data' && (
                <span className="text-xs text-muted-foreground">—</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
