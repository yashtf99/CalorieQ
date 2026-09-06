import { cn } from '@/lib/utils'

interface MacroBarProps {
  label: string
  value: number
  target: number | null
  color: string
  unit?: string
}

function MacroBar({ label, value, target, color, unit = 'g' }: MacroBarProps) {
  const pct = target ? Math.min((value / target) * 100, 100) : 0

  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className="text-sm font-medium tabular-nums">
          <span className={cn(value > 0 ? 'text-foreground' : 'text-muted-foreground')}>
            {value % 1 === 0 ? value : value.toFixed(1)}{unit}
          </span>
          {target && (
            <span className="text-muted-foreground font-normal"> / {target}{unit}</span>
          )}
        </span>
      </div>
      <div className="h-2 rounded-full bg-border overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: target ? `${pct}%` : '0%', backgroundColor: color }}
        />
      </div>
      {target && (
        <div className="flex justify-end">
          <span className="text-xs text-muted-foreground tabular-nums">{Math.round(pct)}%</span>
        </div>
      )}
    </div>
  )
}

interface Props {
  consumed: {
    protein_g: number
    carb_g: number
    fat_g: number
    fibre_g: number
  }
  goal: {
    protein_g: number | null
    carbs_g: number | null
    fat_g: number | null
    fibre_g: number | null
  } | null
}

export default function MacroCard({ consumed, goal }: Props) {
  return (
    <div className="bg-card border border-border rounded-xl p-5 space-y-4">
      <h3 className="text-sm font-medium text-foreground">Today's Nutrition</h3>
      <div className="space-y-4">
        <MacroBar
          label="Protein"
          value={consumed.protein_g}
          target={goal?.protein_g ?? null}
          color="oklch(0.65 0.18 230)"   /* blue */
        />
        <MacroBar
          label="Carbohydrates"
          value={consumed.carb_g}
          target={goal?.carbs_g ?? null}
          color="oklch(0.78 0.18 80)"    /* amber */
        />
        <MacroBar
          label="Fat"
          value={consumed.fat_g}
          target={goal?.fat_g ?? null}
          color="oklch(0.68 0.20 20)"    /* rose */
        />
        <MacroBar
          label="Fibre"
          value={consumed.fibre_g}
          target={goal?.fibre_g ?? null}
          color="oklch(0.72 0.18 145)"   /* green */
        />
      </div>
    </div>
  )
}
