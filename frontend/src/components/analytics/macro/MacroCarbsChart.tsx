import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { WeeklyReportOut } from '@/types/reports'

interface Props {
  data: WeeklyReportOut[]
}

export default function MacroCarbsChart({ data }: Props) {
  const chartData = data.flatMap(week =>
    week.data.map((day) => ({
      date: day.date.slice(5), // MM-DD
      carbs: day.carb_g,
    }))
  )

  const avgCarbs = chartData.length > 0
    ? Math.round(chartData.reduce((sum, d) => sum + d.carbs, 0) / chartData.length)
    : 0

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-1">Carbs Trend</h3>
        <p className="text-xs text-muted-foreground">Avg: {avgCarbs} g/day</p>
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
          <Line
            type="monotone"
            dataKey="carbs"
            stroke="oklch(0.78 0.18 80)"
            dot={{ fill: 'oklch(0.78 0.18 80)', r: 4 }}
            activeDot={{ r: 6 }}
            name="Carbs (g)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}