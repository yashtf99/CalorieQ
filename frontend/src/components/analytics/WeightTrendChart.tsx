import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { parseISO } from 'date-fns'
import { USER_TZ } from '@/lib/tz'

interface Props {
  logs: Array<{ logged_at: string; weight_kg: number }>
  goalWeight?: number
}

function formatInUserTz(isoString: string): { time: string; full: string } {
  const date = parseISO(isoString)
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: USER_TZ,
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
  const parts = formatter.formatToParts(date)
  const timeStr = `${parts.find(p => p.type === 'hour')?.value}:${parts.find(p => p.type === 'minute')?.value}`
  const fullStr = formatter.format(date)
  return { time: timeStr, full: fullStr }
}

function CustomTooltip({ active, payload }: any) {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-card border border-border rounded p-2 text-xs">
        <p className="font-medium">{data.timestamp}</p>
        <p className="text-muted-foreground text-xs">Timezone: {USER_TZ}</p>
        <p className="text-primary">Weight: {data.weight} kg</p>
      </div>
    )
  }
  return null
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

  // Sort logs by date ascending for chart
  const sortedLogs = [...logs].sort((a, b) => a.logged_at.localeCompare(b.logged_at))

  const chartData = sortedLogs.map((log) => {
    const { time, full } = formatInUserTz(log.logged_at)
    return {
      id: `${log.logged_at}`,
      timestamp: full,
      xAxisLabel: time,
      weight: parseFloat(log.weight_kg.toFixed(1)),
      logged_at: log.logged_at,
    }
  })

  const avgWeight = (sortedLogs.reduce((sum, l) => sum + l.weight_kg, 0) / sortedLogs.length).toFixed(1)
  const currentWeight = sortedLogs[sortedLogs.length - 1]?.weight_kg.toFixed(1)
  const startWeight = sortedLogs[0]?.weight_kg.toFixed(1)
  const change = startWeight && currentWeight
    ? ((parseFloat(currentWeight) - parseFloat(startWeight)) / parseFloat(startWeight) * 100).toFixed(1)
    : '0'

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
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
          <XAxis
            dataKey="xAxisLabel"
            stroke="var(--color-muted-foreground)"
            style={{ fontSize: '12px' }}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis
            stroke="var(--color-muted-foreground)"
            style={{ fontSize: '12px' }}
            domain={['dataMin - 1', 'dataMax + 1']}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          {goalWeight && (
            <ReferenceLine
              y={goalWeight}
              stroke="var(--color-muted-foreground)"
              strokeDasharray="5 5"
              label={{ value: `Goal: ${goalWeight}kg`, position: 'right', fill: 'var(--color-muted-foreground)', fontSize: 11 }}
            />
          )}
          <Line
            type="linear"
            dataKey="weight"
            stroke="var(--color-primary)"
            dot={{ fill: 'var(--color-primary)', r: 5 }}
            activeDot={{ r: 7 }}
            name="Weight (kg)"
            isAnimationActive={true}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
