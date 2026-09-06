import type { MicrosReportOut } from '@/types/reports'

interface Props {
  report: MicrosReportOut
}

export default function MicrosTable({ report }: Props) {
  const entries = Object.entries(report.totals)
    .filter(([key]) => !['id', 'start', 'end'].includes(key))
    .sort(([a], [b]) => a.localeCompare(b))

  if (entries.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-4">
        <h3 className="text-sm font-semibold mb-4">Micronutrients</h3>
        <p className="text-sm text-muted-foreground">No micronutrient data available</p>
      </div>
    )
  }

  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <h3 className="text-sm font-semibold mb-4">Micronutrients</h3>
      <p className="text-xs text-muted-foreground mb-3">Data from food database entries only (excludes free-form meals)</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-2 px-2 font-medium">Nutrient</th>
              <th className="text-right py-2 px-2 font-medium">Total</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([key, value]) => (
              <tr key={key} className="border-b border-border last:border-0 hover:bg-muted/50">
                <td className="py-2 px-2 text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</td>
                <td className="py-2 px-2 text-right font-medium">
                  {value === null || value === undefined ? '—' : typeof value === 'number' ? value.toFixed(1) : value}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
