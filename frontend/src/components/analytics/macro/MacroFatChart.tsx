import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { WeeklyReportOut } from '@/types/reports'

interface Props {
  data: WeeklyReportOut[]
}

export default function MacroFatChart({ data }: Props) {
  const chartData = data.flatMap(week =>
    week.data.map((day) => ({
      date: day.date.slice(5), // MM-DD
      fat: day.fat_g,
    }))
  )

  const avgFat = chartData.length > 0
    ? Math.round(chartData.reduce((sum, d) => sum + d.fat, 0) / chartData.length)
    : 0

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-1">Fat Trend</h3>
        <p className="text-xs text-muted-foreground">Avg: {avgFat} g/day</p>
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
            dataKey="fat"
            stroke="oklch(0.68 0.20 20)"
            dot={{ fill: 'oklch(0.68 0.20 20)', r: 4 }}
            activeDot={{ r: 6 }}
            name="Fat (g)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}