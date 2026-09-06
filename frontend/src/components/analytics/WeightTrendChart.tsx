import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'

interface Props {
  logs: Array<{ logged_at: string; weight_kg: number }>
  goalWeight?: number
}

export default function WeightTrendChart({ logs, goalWeight }: Props) {
  if (!logs || logs.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-4">
        <h3 className="text-sm font-semibold mb-4">Weight Trend</h3>
        <div className="h-60 flex items-center justify-center text-muted-foreground text-sm">
          No weight logs available
        </div>
      </div>
    )
  }

  const chartData = logs.map((log) => ({
    date: log.logged_at.slice(5, 10),
    weight: log.weight_kg,
  }))

  const avgWeight = (logs.reduce((sum, l) => sum + l.weight_kg, 0) / logs.length).toFixed(1)
  const currentWeight = logs[logs.length - 1]?.weight_kg.toFixed(1)
  const startWeight = logs[0]?.weight_kg.toFixed(1)
  const change = ((parseFloat(currentWeight!) - parseFloat(startWeight!)) / parseFloat(startWeight!) * 100).toFixed(1)

  return (
    <div className="bg-card border border-border rounded-xl p-4 space-y-4">
      <div>
        <h3 className="text-sm font-semibold mb-2">Weight Trend</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs mb-4">
          <div>
            <p className="text-muted-foreground">Start</p>
            <p className="font-medium">{startWeight} kg</p>
          </div>
          <div>
            <p className="text-muted-foreground">Current</p>
            <p className="font-medium">{currentWeight} kg</p>
          </div>
          <div>
            <p className="text-muted-foreground">Avg</p>
            <p className="font-medium">{avgWeight} kg</p>
          </div>
          <div>
            <p className="text-muted-foreground">Change</p>
            <p className={`font-medium ${parseFloat(change) < 0 ? 'text-primary' : 'text-muted-foreground'}`}>
              {change}%
            </p>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={250}>
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
          {goalWeight && (
            <ReferenceLine
              y={goalWeight}
              stroke="var(--color-muted-foreground)"
              strokeDasharray="5 5"
              label={{ value: 'Goal', position: 'right', fill: 'var(--color-muted-foreground)', fontSize: 11 }}
            />
          )}
          <Line
            type="monotone"
            dataKey="weight"
            stroke="var(--color-primary)"
            dot={{ fill: 'var(--color-primary)', r: 4 }}
            activeDot={{ r: 6 }}
            name="Weight (kg)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
