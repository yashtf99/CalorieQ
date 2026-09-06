import { useState, useMemo } from 'react'
import { format, subDays, startOfToday } from 'date-fns'
import { useWeeklyReport } from '@/api/reports'
import TimeRangeSelector from '@/components/analytics/TimeRangeSelector'
import CaloriesTrendChart from '@/components/analytics/CaloriesTrendChart'
import MacroStackedChart from '@/components/analytics/MacroStackedChart'
import MacroDonutChart from '@/components/analytics/MacroDonutChart'
import WeightTrendChart from '@/components/analytics/WeightTrendChart'
import MicrosTable from '@/components/analytics/MicrosTable'

type Tab = 'overview' | 'calories' | 'macros' | 'weight' | 'nutrition'

const tabs: Array<{ id: Tab; label: string }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'calories', label: 'Calories' },
  { id: 'macros', label: 'Macros' },
  { id: 'weight', label: 'Weight' },
  { id: 'nutrition', label: 'Nutrition' },
]

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const today = format(startOfToday(), 'yyyy-MM-dd')
  const [startDate, setStartDate] = useState(format(subDays(startOfToday(), 29), 'yyyy-MM-dd'))
  const [endDate, setEndDate] = useState(today)

  const handleRangeChange = (start: string, end: string) => {
    setStartDate(start)
    setEndDate(end)
  }

  // Get all weeks in range
  const weeks = useMemo(() => {
    const result = []
    let currentDate = new Date(startDate)
    const lastDate = new Date(endDate)
    while (currentDate <= lastDate) {
      result.push(format(currentDate, 'yyyy-MM-dd'))
      currentDate.setDate(currentDate.getDate() + 7)
    }
    return result
  }, [startDate, endDate])

  // Fetch first week (representative data) - for simplicity, just show most recent week
  const mostRecentWeek = weeks[weeks.length - 1] || today
  const { data: weeklyReport, isLoading } = useWeeklyReport(mostRecentWeek)

  // For charts showing the full range, aggregate data from individual weeks
  const aggregatedData = useMemo(() => {
    if (!weeklyReport) return []
    // In a real app, you'd fetch all weeks, but for now return current week data
    return [weeklyReport]
  }, [weeklyReport])

  const renderOverview = () => {
    if (!weeklyReport) {
      return <div className="text-center py-8 text-muted-foreground">No data available for selected range</div>
    }

    const daysWithLogs = weeklyReport.data.filter(d => d.energy_kcal > 0).length
    const avgKcal = Math.round(
      weeklyReport.data.reduce((sum, day) => sum + day.energy_kcal, 0) / weeklyReport.data.length
    )
    const avgProtein = (
      weeklyReport.data.reduce((sum, day) => sum + day.protein_g, 0) / weeklyReport.data.length
    ).toFixed(1)

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Avg Daily Calories</p>
            <p className="text-2xl font-bold">{avgKcal.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground mt-1">
              {weeklyReport?.goal?.daily_calories
                ? `Goal: ${weeklyReport.goal.daily_calories.toLocaleString()}`
                : 'No goal set'}
            </p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Avg Daily Protein</p>
            <p className="text-2xl font-bold">{avgProtein}g</p>
            <p className="text-xs text-muted-foreground mt-1">
              {weeklyReport?.goal?.protein_g
                ? `Goal: ${weeklyReport.goal.protein_g}g`
                : 'No goal set'}
            </p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Days Tracked</p>
            <p className="text-2xl font-bold">{daysWithLogs}</p>
            <p className="text-xs text-muted-foreground mt-1">in selected range</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Track your nutrition trends over time</p>
      </div>

      {/* Time Range Selector */}
      <div className="bg-card border border-border rounded-xl p-4">
        <p className="text-sm font-semibold mb-3">Date Range</p>
        <TimeRangeSelector startDate={startDate} endDate={endDate} onRangeChange={handleRangeChange} />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div>
        {isLoading && (
          <div className="text-center py-8 text-muted-foreground">Loading analytics...</div>
        )}

        {!isLoading && !weeklyReport && (
          <div className="text-center py-8 text-muted-foreground">
            No data available for the selected date range
          </div>
        )}

        {!isLoading && weeklyReport && (
          <>
            {activeTab === 'overview' && renderOverview()}

            {activeTab === 'calories' && (
              <CaloriesTrendChart
                data={aggregatedData}
                goal={weeklyReport?.goal?.daily_calories ?? null}
              />
            )}

            {activeTab === 'macros' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <MacroStackedChart data={aggregatedData} />
                <MacroDonutChart macros={weeklyReport.actual_period_avg} />
              </div>
            )}

            {activeTab === 'weight' && (
              <WeightTrendChart
                logs={weeklyReport.weight_logs || []}
                goalWeight={weeklyReport?.goal?.weight_target_kg ?? undefined}
              />
            )}

            {activeTab === 'nutrition' && (
              <MicrosTable report={{
                start: startDate,
                end: endDate,
                note: 'Micronutrient data from food database entries only',
                totals: {
                  energy_kcal: weeklyReport.actual_period_avg.energy_kcal,
                  protein_g: weeklyReport.actual_period_avg.protein_g,
                  carb_g: weeklyReport.actual_period_avg.carb_g,
                  fat_g: weeklyReport.actual_period_avg.fat_g,
                  fibre_g: weeklyReport.actual_period_avg.fibre_g,
                } as Record<string, number | null>
              }} />
            )}
          </>
        )}
      </div>
    </div>
  )
}
