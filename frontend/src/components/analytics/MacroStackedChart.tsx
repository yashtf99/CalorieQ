import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { WeeklyReportOut } from '@/types/reports'

interface Props {
  data: WeeklyReportOut[]
}

export default function MacroStackedChart({ data }: Props) {
  const chartData = data.flatMap(week =>
    week.data.map((day) => ({
      date: day.date.slice(5),
      protein: day.protein_g,
      carbs: day.carb_g,
      fat: day.fat_g,
    }))
  )

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <h3 className="text-sm font-semibold mb-4">Macronutrients Over Time</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
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
          <Bar dataKey="protein" fill="oklch(0.65 0.18 230)" name="Protein (g)" />
          <Bar dataKey="carbs" fill="oklch(0.78 0.18 80)" name="Carbs (g)" />
          <Bar dataKey="fat" fill="oklch(0.68 0.20 20)" name="Fat (g)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
