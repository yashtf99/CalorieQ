import type { WeeklyReportOut } from '@/types/reports'
import { format, parseISO } from 'date-fns'
import { useActiveGoal } from '@/api/goals'

interface Props {
  report: WeeklyReportOut | null
}

interface MacroBarProps {
  label: string
  value: number
  color: string
  goalValue?: number | null
}

function MacroBar({ label, value, color, goalValue }: MacroBarProps) {
  const pct = goalValue ? Math.min((value / goalValue) * 100, 100) : 0

  return (
    <div className="flex items-center gap-1.5">
      <span className="text-xs font-medium w-4 text-muted-foreground">{label}</span>
      <div className="flex-1 h-1 rounded-full bg-border overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs font-medium w-7 text-right text-foreground">{Math.round(value)}g</span>
    </div>
  )
}

const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export default function ThisWeekView({ report }: Props) {
  const { data: activeGoal } = useActiveGoal()

  if (!report) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No data available
      </div>
    )
  }

  const effectiveGoal = report.goal || activeGoal

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-2">
        {report.data.map((day, index) => {
          const hasData = day.energy_kcal > 0
          const caloriesMet = effectiveGoal?.daily_calories
            ? day.energy_kcal >= effectiveGoal.daily_calories
            : false
          const borderColor = caloriesMet ? 'border-primary' : 'border-border'
          const bgColor = caloriesMet ? 'bg-primary/5' : 'bg-muted/30'

          return (
            <div
              key={day.date}
              className={`bg-card border-2 ${borderColor} ${bgColor} rounded-lg p-3 flex flex-col items-center space-y-2 transition-all hover:shadow-md`}
            >
              {/* Day label */}
              <div className="text-center">
                <p className="text-xs font-semibold text-foreground">{dayLabels[index]}</p>
                <p className="text-xs text-muted-foreground">{format(parseISO(day.date), 'MMM dd')}</p>
              </div>

              {/* Calorie circle */}
              <div className="w-16 h-16 rounded-full flex flex-col items-center justify-center border-2 border-primary/20 bg-primary/5">
                <p className="text-sm font-bold text-foreground text-center">
                  {Math.round(day.energy_kcal)}
                </p>
                <p className="text-xs text-muted-foreground">kcal</p>
              </div>

              {/* Macros with bars */}
              <div className="w-full space-y-1.5">
                <MacroBar label="P" value={day.protein_g} color="oklch(0.65 0.18 230)" goalValue={effectiveGoal?.protein_g} />
                <MacroBar label="C" value={day.carb_g} color="oklch(0.78 0.18 80)" goalValue={effectiveGoal?.carbs_g} />
                <MacroBar label="F" value={day.fat_g} color="oklch(0.68 0.20 20)" goalValue={effectiveGoal?.fat_g} />
              </div>

              {/* Status indicator */}
              {hasData && (
                <div className="w-full">
                  <div className="h-0.5 rounded-full bg-border overflow-hidden">
                    <div
                      className={`h-full transition-all ${caloriesMet ? 'bg-primary' : 'bg-muted'}`}
                      style={{
                        width: effectiveGoal?.daily_calories
                          ? `${Math.min((day.energy_kcal / effectiveGoal.daily_calories) * 100, 100)}%`
                          : '100%',
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

    </div>
  )
}
