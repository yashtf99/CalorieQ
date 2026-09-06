import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'
import type { WeeklyReportOut } from '@/types/reports'

interface Props {
  report: WeeklyReportOut
}

export default function WeeklyCaloriesChart({ report }: Props) {
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const data = report.data.map((day, i) => ({
    day: days[i],
    kcal: day.energy_kcal,
  }))

  const avgKcal = Math.round(report.actual_period_avg.energy_kcal)

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <h3 className="text-sm font-semibold mb-4">Weekly Calories</h3>
      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
          <XAxis dataKey="day" stroke="var(--color-muted-foreground)" style={{ fontSize: '12px' }} />
          <YAxis hide />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-card)',
              border: '1px solid var(--color-border)',
              borderRadius: '6px',
            }}
          />
          {report.goal?.daily_calories && (
            <ReferenceLine
              y={report.goal.daily_calories}
              stroke="var(--color-muted-foreground)"
              strokeDasharray="5 5"
              label={{ value: 'Goal', position: 'right', fill: 'var(--color-muted-foreground)', fontSize: 11 }}
            />
          )}
          <Bar dataKey="kcal" fill="var(--color-primary)" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-3 text-right text-xs text-muted-foreground">
        Avg: {avgKcal.toLocaleString()} kcal/day
      </div>
    </div>
  )
}
