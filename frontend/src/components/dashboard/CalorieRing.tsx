import { Flame } from 'lucide-react'
import { getCalorieState, pickMessage } from '@/lib/calorieMessages'

interface Props {
  consumed: number
  goal: number | null
}

const RADIUS = 46
const STROKE = 7
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

function ringColor(state: string | null) {
  switch (state) {
    case 'on_track': return 'var(--color-primary)'
    case 'near_goal': return 'oklch(0.78 0.18 80)'
    case 'over': return 'oklch(0.78 0.18 80)'
    case 'exceeded': return 'var(--color-destructive)'
    default: return 'var(--color-primary)'
  }
}

export default function CalorieRing({ consumed, goal }: Props) {
  const pct = goal ? Math.min(consumed / goal, 1.05) : 0
  const filled = Math.min(pct, 1) * CIRCUMFERENCE
  const remaining = goal ? goal - consumed : null
  const state = goal ? getCalorieState(pct) : null
  const color = state ? ringColor(state) : 'var(--color-primary)'
  const message = state ? pickMessage(state) : null
  const size = (RADIUS + STROKE) * 2 + 4

  return (
    <div className="flex items-center gap-5 pl-2 pr-5 py-3">
      {/* Ring on left */}
      <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* track */}
          <circle
            cx={size / 2} cy={size / 2} r={RADIUS}
            fill="none"
            stroke="var(--color-border)"
            strokeWidth={STROKE}
          />
          {/* fill */}
          {consumed > 0 && (
            <circle
              cx={size / 2} cy={size / 2} r={RADIUS}
              fill="none"
              stroke={color}
              strokeWidth={STROKE}
              strokeLinecap="round"
              strokeDasharray={`${filled} ${CIRCUMFERENCE}`}
              style={{ transition: 'stroke-dasharray 0.6s ease' }}
            />
          )}
        </svg>

        {/* centre text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-xl font-bold tabular-nums leading-none ${consumed === 0 ? 'text-muted-foreground' : ''}`}>
            {consumed.toLocaleString()}
          </span>
          <span className="text-xs text-muted-foreground mt-0.5">kcal</span>
        </div>
      </div>

      {/* Info on right */}
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <Flame
            className="w-5 h-5 flex-shrink-0"
            style={{
              color,
              filter: 'drop-shadow(0 0 8px currentColor)',
            }}
          />
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Calories</span>
        </div>
        {goal && (
          <>
            <div>
              <p className="text-xl font-bold tabular-nums">
                {remaining! >= 0 ? remaining!.toLocaleString() : `${Math.abs(remaining!).toLocaleString()}`}
              </p>
              <p className="text-xs text-muted-foreground">{remaining! >= 0 ? 'left' : state === 'over' ? 'over' : 'exceeded'} of {goal.toLocaleString()} goal</p>
            </div>
            {message && (
              <p className={`text-xs ${
                state === 'on_track' || state === 'near_goal' ? 'text-primary' :
                state === 'over' ? 'text-amber-400' :
                'text-destructive'
              }`}>
                {message}
              </p>
            )}
          </>
        )}
        {!goal && (
          <p className="text-xs text-muted-foreground">Set a goal in Profile</p>
        )}
      </div>
    </div>
  )
}
