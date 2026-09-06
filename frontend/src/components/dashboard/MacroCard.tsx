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
    <div className="space-y-0.5">
      <div className="flex items-baseline justify-between">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="text-xs font-medium tabular-nums">
          {value % 1 === 0 ? value : value.toFixed(1)}{unit}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-border overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: target ? `${pct}%` : '0%', backgroundColor: color }}
        />
      </div>
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
    <div className="bg-card border border-border rounded-xl px-4 py-3 space-y-2.5">
      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Nutrition</h3>
      <div className="space-y-2.5">
        <MacroBar
          label="Protein"
          value={consumed.protein_g}
          target={goal?.protein_g ?? null}
          color="oklch(0.65 0.18 230)"
        />
        <MacroBar
          label="Carbs"
          value={consumed.carb_g}
          target={goal?.carbs_g ?? null}
          color="oklch(0.78 0.18 80)"
        />
        <MacroBar
          label="Fat"
          value={consumed.fat_g}
          target={goal?.fat_g ?? null}
          color="oklch(0.68 0.20 20)"
        />
        <MacroBar
          label="Fibre"
          value={consumed.fibre_g}
          target={goal?.fibre_g ?? null}
          color="oklch(0.72 0.18 145)"
        />
      </div>
    </div>
  )
}
