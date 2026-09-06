import { useState } from 'react'
import { format, startOfToday, startOfWeek, endOfWeek, addWeeks, subDays } from 'date-fns'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useWeeklyReportRange, useMicrosReport } from '@/api/reports'
import TimeRangeSelector from '@/components/analytics/TimeRangeSelector'
import ThisWeekView from '@/components/analytics/ThisWeekView'
import CaloriesTrendChart from '@/components/analytics/CaloriesTrendChart'
import MicrosTable from '@/components/analytics/MicrosTable'
import MacroProteinChart from '@/components/analytics/macro/MacroProteinChart'
import MacroCarbsChart from '@/components/analytics/macro/MacroCarbsChart'
import MacroFatChart from '@/components/analytics/macro/MacroFatChart'

type Tab = 'overview' | 'calories' | 'macros' | 'nutrition'

const tabs: Array<{ id: Tab; label: string }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'calories', label: 'Calories' },
  { id: 'macros', label: 'Macros' },
  { id: 'nutrition', label: 'Nutrition' },
]

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const today = startOfToday()

  // Week navigation
  const [weekOffset, setWeekOffset] = useState(0)
  const displayDate = addWeeks(today, weekOffset)

  // This Week (shows full week Sun-Sat, not affected by filter)
  const weekStart = startOfWeek(displayDate, { weekStartsOn: 0 })
  const weekEnd = endOfWeek(displayDate, { weekStartsOn: 0 })
  const weekStartStr = format(weekStart, 'yyyy-MM-dd')
  const weekEndStr = format(weekEnd, 'yyyy-MM-dd')

  // Date filter (for other tabs, defaults to 7d preset)
  const defaultStart = format(subDays(today, 6), 'yyyy-MM-dd')
  const defaultEnd = format(today, 'yyyy-MM-dd')
  const [startDate, setStartDate] = useState(defaultStart)
  const [endDate, setEndDate] = useState(defaultEnd)

  const handlePrevWeek = () => setWeekOffset(prev => prev - 1)
  const handleNextWeek = () => setWeekOffset(prev => prev + 1)

  const handleRangeChange = (start: string, end: string) => {
    setStartDate(start)
    setEndDate(end)
  }

  // Fetch data for This Week (full week Sun-Sat)
  const { data: weeklyReport, isLoading: isLoadingWeekly } = useWeeklyReportRange(weekStartStr, weekEndStr)

  // Fetch data for filtered range (for Overview/Calories/etc)
  const { data: filteredReport, isLoading: isLoadingFiltered } = useWeeklyReportRange(startDate, endDate)
  const { data: microsReport, isLoading: isLoadingMicros } = useMicrosReport(startDate, endDate)

  const isLoading = isLoadingWeekly
  const isFilteredLoading = isLoadingFiltered || isLoadingMicros

  const renderOverview = () => {
    if (!filteredReport) {
      return <div className="text-center py-8 text-muted-foreground">No data available for selected range</div>
    }

    const daysWithLogs = filteredReport.data.filter(d => d.energy_kcal > 0).length
    const avgKcal = Math.round(
      filteredReport.data.reduce((sum, d) => sum + d.energy_kcal, 0) /
      (daysWithLogs || 1)
    )
    const avgProtein = (
      filteredReport.data.reduce((sum, d) => sum + d.protein_g, 0) /
      (daysWithLogs || 1)
    ).toFixed(1)

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Avg Daily Calories</p>
            <p className="text-2xl font-bold">{avgKcal.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground mt-1">
              {filteredReport?.goal?.daily_calories
                ? `Goal: ${filteredReport.goal.daily_calories.toLocaleString()}`
                : 'No goal set'}
            </p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Avg Daily Protein</p>
            <p className="text-2xl font-bold">{avgProtein}g</p>
            <p className="text-xs text-muted-foreground mt-1">
              {filteredReport?.goal?.protein_g
                ? `Goal: ${filteredReport.goal.protein_g}g`
                : 'No goal set'}
            </p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Days Tracked</p>
            <p className="text-2xl font-bold">{daysWithLogs}</p>
            <p className="text-xs text-muted-foreground mt-1">days with logs</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Date Range</p>
            <p className="text-2xl font-bold">{filteredReport.data.length}</p>
            <p className="text-xs text-muted-foreground mt-1">days in range</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header - Goal Calories + Filter in same row */}
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold text-foreground">
          Goal Calories {filteredReport?.goal?.daily_calories && `• ${filteredReport.goal.daily_calories.toLocaleString()} kcal`}
        </h1>
        <div className="flex-shrink-0">
          <TimeRangeSelector startDate={startDate} endDate={endDate} onRangeChange={handleRangeChange} />
        </div>
      </div>

      {/* This Week Section - Always visible, not affected by filter */}
      {isLoading ? (
        <div className="text-center py-8 text-muted-foreground">Loading...</div>
      ) : weeklyReport ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              {format(weekStart, 'MMM dd')} – {format(weekEnd, 'MMM dd')}
            </p>
            <div className="flex gap-1">
              <button
                onClick={handlePrevWeek}
                className="p-1.5 hover:bg-muted rounded transition-colors"
                title="Previous week"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={handleNextWeek}
                disabled={weekOffset >= 0}
                className="p-1.5 hover:bg-muted rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Next week"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
          <ThisWeekView report={weeklyReport} />
        </div>
      ) : null}

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

      {/* Content - Changes based on date filter */}
      <div>
        {isFilteredLoading && (
          <div className="text-center py-8 text-muted-foreground">Loading...</div>
        )}

        {!isFilteredLoading && !filteredReport && (
          <div className="text-center py-8 text-muted-foreground">
            No data available for the selected date range
          </div>
        )}

        {!isFilteredLoading && filteredReport && (
          <>
            {activeTab === 'overview' && renderOverview()}

            {activeTab === 'calories' && (
              <CaloriesTrendChart
                data={[filteredReport]}
                goal={filteredReport?.goal?.daily_calories ?? null}
              />
            )}

            {activeTab === 'macros' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MacroProteinChart data={[filteredReport]} />
                <MacroCarbsChart data={[filteredReport]} />
                <MacroFatChart data={[filteredReport]} />
              </div>
            )}

            {activeTab === 'nutrition' && microsReport && (
              <MicrosTable report={microsReport} />
            )}
          </>
        )}
      </div>
    </div>
  )
}
