import { cn } from '@/lib/utils'

interface Props {
  consumed: number
  goal: number | null
}

const RADIUS = 72
const STROKE = 10
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

function ringColor(pct: number) {
  if (pct >= 1.05) return 'var(--color-destructive)'
  if (pct >= 0.9)  return 'oklch(0.78 0.18 80)'  // amber
  return 'var(--color-primary)'                    // green
}

export default function CalorieRing({ consumed, goal }: Props) {
  const pct       = goal ? Math.min(consumed / goal, 1.05) : 0
  const filled    = Math.min(pct, 1) * CIRCUMFERENCE
  const remaining = goal ? goal - consumed : null
  const color     = goal ? ringColor(pct) : 'var(--color-primary)'
  const size      = (RADIUS + STROKE) * 2 + 4

  return (
    <div className="flex flex-col items-center justify-center gap-4 py-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* track */}
          <circle
            cx={size / 2} cy={size / 2} r={RADIUS}
            fill="none"
            stroke="var(--color-border)"
            strokeWidth={STROKE}
          />
          {/* fill — always green up to 100%, stays capped */}
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
          <span className={cn('text-4xl font-bold tabular-nums leading-none', consumed === 0 && 'text-muted-foreground')}>
            {consumed.toLocaleString()}
          </span>
          <span className="text-xs text-muted-foreground mt-1">kcal eaten</span>
          {goal && (
            <span className="text-xs text-muted-foreground">of {goal.toLocaleString()}</span>
          )}
        </div>
      </div>

      {/* remaining / exceeded label */}
      {goal && (
        <div className="text-center">
          {remaining! >= 0 ? (
            <p className="text-sm text-muted-foreground">
              <span className="text-foreground font-semibold">{remaining!.toLocaleString()} kcal</span> remaining
            </p>
          ) : (
            <p className="text-sm text-destructive font-semibold">
              {Math.abs(remaining!).toLocaleString()} kcal over goal
            </p>
          )}
        </div>
      )}

      {!goal && (
        <p className="text-xs text-muted-foreground text-center max-w-[160px]">
          No goal set — go to Profile to set a daily target
        </p>
      )}
    </div>
  )
}
