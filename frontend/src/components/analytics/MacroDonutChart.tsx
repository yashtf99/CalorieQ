import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts'
import type { MacroTotals } from '@/types/reports'

interface Props {
  macros: MacroTotals
}

export default function MacroDonutChart({ macros }: Props) {
  const data = [
    { name: 'Protein', value: Math.round(macros.protein_g * 4) },
    { name: 'Carbs', value: Math.round(macros.carb_g * 4) },
    { name: 'Fat', value: Math.round(macros.fat_g * 9) },
  ]

  const colors = ['oklch(0.65 0.18 230)', 'oklch(0.78 0.18 80)', 'oklch(0.68 0.20 20)']

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <h3 className="text-sm font-semibold mb-4">Macro Distribution (by kcal)</h3>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={90}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-card)',
              border: '1px solid var(--color-border)',
              borderRadius: '6px',
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
