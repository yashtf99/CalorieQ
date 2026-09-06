import { useState } from 'react'
import { format, parseISO } from 'date-fns'
import { AlertCircle } from 'lucide-react'
import { useDailySummary } from '@/api/reports'
import CalorieRing from '@/components/dashboard/CalorieRing'
import DateSelector from '@/components/dashboard/DateSelector'
import MacroCard from '@/components/dashboard/MacroCard'
import { CalorieRingSkeleton, MacroCardSkeleton } from '@/components/dashboard/SummarySkeletons'
import OnboardingWizard from '@/components/onboarding/OnboardingWizard'
import { useAuthStore } from '@/store/authStore'
import { useDateStore } from '@/store/dateStore'

const ONBOARDING_SKIP_KEY = 'calorieq_onboarding_skipped'

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const selectedDate = useDateStore((s) => s.selectedDate)
  const { data, isLoading, isError, refetch } = useDailySummary(selectedDate)

  const [wizardDismissed, setWizardDismissed] = useState(
    () => localStorage.getItem(ONBOARDING_SKIP_KEY) === 'true',
  )

  const name    = user?.display_name?.split(' ')[0] ?? 'there'
  const isToday = selectedDate === format(new Date(), 'yyyy-MM-dd')

  const showWizard = !isLoading && !wizardDismissed && data?.goal === null

  function dismissWizard() {
    localStorage.setItem(ONBOARDING_SKIP_KEY, 'true')
    setWizardDismissed(true)
  }

  function finishWizard() {
    localStorage.removeItem(ONBOARDING_SKIP_KEY) // skipped → now set, remove flag
    setWizardDismissed(true)
  }

  return (
    <>
      {showWizard && (
        <OnboardingWizard
          userName={name}
          onFinish={finishWizard}
        />
      )}

      <div className="space-y-6">
        {/* header row */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">
              {isToday ? `${greeting()}, ${name}` : format(parseISO(selectedDate), 'EEEE, d MMMM')}
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              {isToday ? "Here's your nutrition today" : 'Viewing a past day'}
            </p>
          </div>
          <DateSelector />
        </div>

        {/* error state */}
        {isError && (
          <div className="flex items-center gap-3 bg-card border border-border rounded-xl p-4 text-sm text-muted-foreground">
            <AlertCircle size={16} className="text-destructive shrink-0" />
            <span>Failed to load summary.</span>
            <button onClick={() => refetch()} className="ml-auto text-primary hover:underline text-sm">
              Retry
            </button>
          </div>
        )}

        {/* calorie ring + macro card */}
        <div className="grid grid-cols-1 md:grid-cols-[2fr_3fr] gap-4">
          <div className="bg-card border border-border rounded-xl flex items-center justify-center min-h-[280px]">
            {isLoading ? (
              <CalorieRingSkeleton />
            ) : data ? (
              <CalorieRing
                consumed={Math.round(data.consumed.energy_kcal)}
                goal={data.goal?.daily_calories ?? null}
              />
            ) : null}
          </div>

          {isLoading ? (
            <MacroCardSkeleton />
          ) : data ? (
            <MacroCard consumed={data.consumed} goal={data.goal} />
          ) : null}
        </div>

        {/* no goal nudge — only shown after wizard skipped */}
        {!isLoading && data && !data.goal && wizardDismissed && (
          <div className="bg-card border border-border rounded-xl p-4 flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Set a daily calorie and macro goal to track your progress.
            </p>
            <div className="flex gap-3 ml-4 shrink-0">
              <button
                onClick={() => setWizardDismissed(false)}
                className="text-sm text-primary hover:underline"
              >
                Set up now
              </button>
              <a href="/profile" className="text-sm text-muted-foreground hover:underline">
                Profile →
              </a>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
