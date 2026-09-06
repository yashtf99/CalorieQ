import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import type { WeeklyReportOut } from '@/types/reports'

interface Props {
  data: WeeklyReportOut[]
  goal: number | null
}

export default function CaloriesTrendChart({ data, goal }: Props) {
  const chartData = data.flatMap(week =>
    week.data.map((day) => ({
      date: day.date.slice(5), // MM-DD
      kcal: day.energy_kcal,
    }))
  )

  const avgKcal = chartData.length > 0
    ? Math.round(chartData.reduce((sum, d) => sum + d.kcal, 0) / chartData.length)
    : 0

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-1">Calorie Trend</h3>
        <p className="text-xs text-muted-foreground">Avg: {avgKcal.toLocaleString()} kcal/day</p>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
          <XAxis dataKey="date" stroke="var(--color-muted-foreground)" style={{ fontSize: '12px' }} />
          <YAxis stroke="var(--color-muted-foreground)" style={{ fontSize: '12px' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-card)',
              border: '1px solid var(--color-border)',
              borderRadius: '6px',
            }}
          />
          <Legend />
          {goal && (
            <ReferenceLine
              y={goal}
              stroke="var(--color-muted-foreground)"
              strokeDasharray="5 5"
              label={{ value: 'Goal', position: 'right', fill: 'var(--color-muted-foreground)', fontSize: 11 }}
            />
          )}
          <Line
            type="monotone"
            dataKey="kcal"
            stroke="var(--color-primary)"
            dot={{ fill: 'var(--color-primary)', r: 4 }}
            activeDot={{ r: 6 }}
            name="Calories"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
