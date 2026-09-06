import type { GoalFormValues } from './StepGoal'

interface Props {
  goal: GoalFormValues
  onFinish: () => void
}

const GOAL_LABEL: Record<string, string> = {
  lose:     'Lose Weight',
  maintain: 'Maintain Weight',
  gain:     'Gain Muscle',
}

export default function StepDone({ goal, onFinish }: Props) {
  return (
    <div className="flex flex-col items-center text-center gap-7">
      {/* animated checkmark ring */}
      <div className="relative w-24 h-24">
        <svg viewBox="0 0 96 96" className="w-full h-full">
          <circle
            cx="48" cy="48" r="40"
            fill="none"
            stroke="var(--color-primary)"
            strokeWidth="6"
            strokeDasharray="251"
            strokeDashoffset="0"
            strokeLinecap="round"
            className="opacity-20"
          />
          <circle
            cx="48" cy="48" r="40"
            fill="none"
            stroke="var(--color-primary)"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray="251"
            strokeDashoffset="0"
            style={{ animation: 'strokeIn 0.6s ease forwards' }}
          />
          <polyline
            points="30,48 43,61 66,36"
            fill="none"
            stroke="var(--color-primary)"
            strokeWidth="5"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ animation: 'fadeIn 0.3s 0.4s ease both' }}
          />
        </svg>
        <style>{`
          @keyframes strokeIn {
            from { stroke-dashoffset: 251 }
            to   { stroke-dashoffset: 0 }
          }
          @keyframes fadeIn {
            from { opacity: 0 }
            to   { opacity: 1 }
          }
        `}</style>
      </div>

      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-foreground">You're all set! 🎉</h2>
        <p className="text-sm text-muted-foreground">
          Your dashboard is now personalised based on your profile.
        </p>
      </div>

      {/* goal summary card */}
      <div className="w-full bg-muted rounded-xl p-4 space-y-3 text-left">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Your goal</span>
          <span className="text-sm font-semibold text-primary">{GOAL_LABEL[goal.goal_type]}</span>
        </div>
        <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
          {[
            { label: 'Calories', value: `${goal.daily_calories.toLocaleString()} kcal` },
            { label: 'Protein',  value: `${goal.protein_g} g` },
            { label: 'Carbs',    value: `${goal.carbs_g} g` },
            { label: 'Fat',      value: `${goal.fat_g} g` },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-baseline justify-between">
              <span className="text-xs text-muted-foreground">{label}</span>
              <span className="text-sm font-medium tabular-nums">{value}</span>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={onFinish}
        className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:opacity-90 active:scale-[0.98] transition-all"
      >
        Let's go →
      </button>
    </div>
  )
}
