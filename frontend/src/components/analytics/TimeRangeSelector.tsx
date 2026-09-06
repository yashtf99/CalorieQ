import { useState } from 'react'
import { format, startOfToday, subDays } from 'date-fns'
import { Calendar } from 'lucide-react'

interface TimeRangeSelectorProps {
  startDate: string
  endDate: string
  onRangeChange: (start: string, end: string) => void
}

export default function TimeRangeSelector({ startDate, endDate, onRangeChange }: TimeRangeSelectorProps) {
  const today = format(startOfToday(), 'yyyy-MM-dd')
  const [showCustom, setShowCustom] = useState(false)
  const [customStart, setCustomStart] = useState(startDate)
  const [customEnd, setCustomEnd] = useState(endDate)

  const presets = [
    { label: '7d', days: 7 },
    { label: '30d', days: 30 },
    { label: '90d', days: 90 },
  ]

  const handlePreset = (days: number) => {
    const end = today
    const start = format(subDays(startOfToday(), days - 1), 'yyyy-MM-dd')
    onRangeChange(start, end)
    setShowCustom(false)
  }

  const handleCustomApply = () => {
    if (customStart >= customEnd) {
      alert('Start date must be before end date')
      return
    }
    const dayDiff = Math.floor((new Date(customEnd).getTime() - new Date(customStart).getTime()) / (1000 * 60 * 60 * 24))
    if (dayDiff > 90) {
      alert('Range cannot exceed 90 days')
      return
    }
    onRangeChange(customStart, customEnd)
    setShowCustom(false)
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {presets.map((preset) => (
        <button
          key={preset.label}
          onClick={() => handlePreset(preset.days)}
          className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
            !showCustom && endDate === today && startDate === format(subDays(startOfToday(), preset.days - 1), 'yyyy-MM-dd')
              ? 'bg-green-500/20 text-green-700 dark:text-green-400 border border-green-500/50'
              : 'bg-muted text-muted-foreground hover:bg-muted/80'
          }`}
        >
          {preset.label}
        </button>
      ))}

      {showCustom ? (
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
            className="px-2 py-1 border border-border rounded text-sm"
          />
          <span className="text-muted-foreground">→</span>
          <input
            type="date"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
            className="px-2 py-1 border border-border rounded text-sm"
          />
          <button
            onClick={handleCustomApply}
            className="px-2 py-1 bg-primary text-primary-foreground rounded text-sm hover:bg-primary/90"
          >
            Apply
          </button>
          <button
            onClick={() => setShowCustom(false)}
            className="px-2 py-1 bg-muted text-muted-foreground rounded text-sm hover:bg-muted/80"
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          onClick={() => {
            setShowCustom(true)
            setCustomStart(startDate)
            setCustomEnd(endDate)
          }}
          className="px-3 py-1.5 rounded text-sm font-medium bg-muted text-muted-foreground hover:bg-muted/80 transition-colors flex items-center gap-1"
        >
          <Calendar className="w-4 h-4" />
          Custom
        </button>
      )}
    </div>
  )
}
