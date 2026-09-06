import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { WeeklyReportOut } from '@/types/reports'

interface Props {
  data: WeeklyReportOut[]
}

export default function MacroProteinChart({ data }: Props) {
  const chartData = data.flatMap(week =>
    week.data.map((day) => ({
      date: day.date.slice(5), // MM-DD
      protein: day.protein_g,
    }))
  )

  const avgProtein = chartData.length > 0
    ? Math.round(chartData.reduce((sum, d) => sum + d.protein, 0) / chartData.length)
    : 0

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-1">Protein Trend</h3>
        <p className="text-xs text-muted-foreground">Avg: {avgProtein} g/day</p>
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
            dataKey="protein"
            stroke="oklch(0.65 0.18 230)"
            dot={{ fill: 'oklch(0.65 0.18 230)', r: 4 }}
            activeDot={{ r: 6 }}
            name="Protein (g)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}