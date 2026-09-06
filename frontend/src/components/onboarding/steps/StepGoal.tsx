import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { GoalSuggestionOut, GoalType } from '@/types/goals'

const schema = z.object({
  goal_type:      z.enum(['lose', 'maintain', 'gain']),
  daily_calories: z.number({ invalid_type_error: 'Required' }).min(1).max(14999),
  protein_g:      z.number({ invalid_type_error: 'Required' }).min(0),
  carbs_g:        z.number({ invalid_type_error: 'Required' }).min(0),
  fat_g:          z.number({ invalid_type_error: 'Required' }).min(0),
  fibre_g:        z.number({ invalid_type_error: 'Required' }).min(0),
})
export type GoalFormValues = z.infer<typeof schema>

const GOAL_TYPES: { value: GoalType; label: string; desc: string; icon: string; color: string }[] = [
  { value: 'lose',     label: 'Lose Weight',    desc: '−500 kcal/day',   icon: '↓', color: 'oklch(0.65 0.18 230)' },
  { value: 'maintain', label: 'Stay Steady',    desc: 'TDEE',            icon: '↔', color: 'oklch(0.72 0.18 145)' },
  { value: 'gain',     label: 'Gain Muscle',    desc: '+300 kcal/day',   icon: '↑', color: 'oklch(0.62 0.22 290)' },
]

interface Props {
  suggestion: GoalSuggestionOut | undefined
  isSuggestionLoading: boolean
  onDone: (data: GoalFormValues) => void
  onBack: () => void
}

export default function StepGoal({ suggestion, isSuggestionLoading, onDone, onBack }: Props) {
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<GoalFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { goal_type: 'maintain' },
  })

  const selectedGoalType = watch('goal_type')

  // Pre-fill macros whenever suggestion loads or goal type changes
  useEffect(() => {
    if (!suggestion) return
    const s = suggestion.suggestions[selectedGoalType]
    setValue('daily_calories', s.daily_calories)
    setValue('protein_g',      s.protein_g)
    setValue('carbs_g',        s.carbs_g)
    setValue('fat_g',          s.fat_g)
    setValue('fibre_g',        s.fibre_g)
  }, [suggestion, selectedGoalType, setValue])

  return (
    <form onSubmit={handleSubmit(onDone)} className="space-y-6">
      <div className="text-center space-y-1">
        <div className="text-3xl mb-2">🎯</div>
        <h2 className="text-xl font-bold text-foreground">Your goal</h2>
        <p className="text-sm text-muted-foreground">We've calculated your TDEE — pick a direction</p>
      </div>

      {/* TDEE chip */}
      {suggestion && (
        <div className="flex justify-center gap-4 text-center">
          <div className="bg-muted rounded-xl px-4 py-2">
            <div className="text-xs text-muted-foreground">BMR</div>
            <div className="text-sm font-semibold tabular-nums">{suggestion.bmr.toLocaleString()} kcal</div>
          </div>
          <div className="bg-primary/10 border border-primary/20 rounded-xl px-4 py-2">
            <div className="text-xs text-muted-foreground">TDEE</div>
            <div className="text-sm font-semibold text-primary tabular-nums">{suggestion.tdee.toLocaleString()} kcal</div>
          </div>
          <div className="bg-muted rounded-xl px-4 py-2">
            <div className="text-xs text-muted-foreground">Formula</div>
            <div className="text-xs font-medium text-muted-foreground">Mifflin-St Jeor</div>
          </div>
        </div>
      )}

      {isSuggestionLoading && (
        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground py-2">
          <Loader2 size={14} className="animate-spin" />
          Calculating your targets…
        </div>
      )}

      {/* Goal type cards */}
      <div className="grid grid-cols-3 gap-2">
        {GOAL_TYPES.map(({ value, label, desc, icon, color }) => (
          <button
            key={value}
            type="button"
            onClick={() => setValue('goal_type', value, { shouldValidate: true })}
            className={cn(
              'flex flex-col items-center gap-1.5 p-3 rounded-xl border text-center transition-all',
              selectedGoalType === value
                ? 'border-2 bg-muted'
                : 'bg-muted/50 border-border hover:border-border/80',
            )}
            style={selectedGoalType === value ? { borderColor: color } : undefined}
          >
            <span className="text-2xl font-bold" style={{ color }}>{icon}</span>
            <span className="text-xs font-semibold text-foreground leading-tight">{label}</span>
            <span className="text-xs text-muted-foreground">{desc}</span>
          </button>
        ))}
      </div>

      {/* Macro targets */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Daily targets</label>
          {suggestion && (
            <span className="text-xs text-muted-foreground">Pre-filled · edit freely</span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-2">
          {[
            { field: 'daily_calories' as const, label: 'Calories', unit: 'kcal', fullWidth: true },
            { field: 'protein_g'      as const, label: 'Protein',  unit: 'g' },
            { field: 'carbs_g'        as const, label: 'Carbs',    unit: 'g' },
            { field: 'fat_g'          as const, label: 'Fat',      unit: 'g' },
            { field: 'fibre_g'        as const, label: 'Fibre',    unit: 'g' },
          ].map(({ field, label, unit, fullWidth }) => (
            <div key={field} className={cn('space-y-1', fullWidth && 'col-span-2')}>
              <label className="text-xs text-muted-foreground">{label}</label>
              <div className="relative">
                <input
                  type="number"
                  {...register(field, { valueAsNumber: true })}
                  className="w-full bg-muted border border-border rounded-xl px-3 py-2 text-sm text-foreground pr-12 focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">{unit}</span>
              </div>
              {errors[field] && <p className="text-xs text-destructive">{errors[field]?.message}</p>}
            </div>
          ))}
        </div>
      </div>

      <button
        type="submit"
        className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:opacity-90 active:scale-[0.98] transition-all"
      >
        Save & continue →
      </button>

      <button type="button" onClick={onBack} className="w-full text-center text-xs text-muted-foreground hover:text-foreground transition-colors">
        ← Back
      </button>
    </form>
  )
}
