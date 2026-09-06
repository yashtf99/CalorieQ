import type { WeeklyReportOut } from '@/types/reports'
import { format, parseISO } from 'date-fns'

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
  const maxValue = goalValue || 50
  const pct = Math.min((value / maxValue) * 100, 100)

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
  if (!report) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No data available
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-2">
        {report.data.map((day, index) => {
          const hasData = day.energy_kcal > 0
          const onTarget = report.goal?.daily_calories
            ? day.energy_kcal <= report.goal.daily_calories
            : true
          const borderColor = !hasData ? 'border-border' : onTarget ? 'border-primary' : 'border-destructive'
          const bgColor = !hasData ? 'bg-muted/30' : onTarget ? 'bg-primary/5' : 'bg-destructive/5'

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
                <MacroBar label="P" value={day.protein_g} color="oklch(0.65 0.18 230)" goalValue={report.goal?.protein_g} />
                <MacroBar label="C" value={day.carb_g} color="oklch(0.78 0.18 80)" goalValue={report.goal?.carbs_g} />
                <MacroBar label="F" value={day.fat_g} color="oklch(0.68 0.20 20)" goalValue={report.goal?.fat_g} />
              </div>

              {/* Status indicator */}
              {hasData && (
                <div className="w-full">
                  <div className="h-0.5 rounded-full bg-border overflow-hidden">
                    <div
                      className={`h-full transition-all ${onTarget ? 'bg-primary' : 'bg-destructive'}`}
                      style={{
                        width: report.goal?.daily_calories
                          ? `${Math.min((day.energy_kcal / report.goal.daily_calories) * 100, 100)}%`
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
