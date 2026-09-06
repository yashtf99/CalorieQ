import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { cn } from '@/lib/utils'
import type { ActivityLevel, Gender } from '@/types/goals'

const schema = z.object({
  height_cm:      z.number({ invalid_type_error: 'Required' }).min(51).max(249),
  weight_kg:      z.number({ invalid_type_error: 'Required' }).min(21).max(499),
  dob:            z.string().min(1, 'Required'),
  gender:         z.enum(['male', 'female', 'other', 'prefer_not_to_say']),
  activity_level: z.enum(['sedentary', 'lightly_active', 'active', 'very_active']),
})
export type ProfileFormValues = z.infer<typeof schema>

const GENDERS: { value: Gender; label: string }[] = [
  { value: 'male',              label: 'Male' },
  { value: 'female',            label: 'Female' },
  { value: 'other',             label: 'Other' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
]

const ACTIVITY_LEVELS: { value: ActivityLevel; label: string; desc: string; icon: string }[] = [
  { value: 'sedentary',      label: 'Sedentary',      desc: 'Little or no exercise',   icon: '🛋️' },
  { value: 'lightly_active', label: 'Lightly Active', desc: '1–3 days / week',          icon: '🚶' },
  { value: 'active',         label: 'Active',          desc: '3–5 days / week',          icon: '🏃' },
  { value: 'very_active',    label: 'Very Active',     desc: '6–7 days / week',          icon: '💪' },
]

interface Props {
  defaultValues?: Partial<ProfileFormValues>
  onNext: (data: ProfileFormValues) => void
  onSkip: () => void
}

export default function StepProfile({ defaultValues, onNext, onSkip }: Props) {
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<ProfileFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { activity_level: 'lightly_active', ...defaultValues },
  })

  const selectedGender   = watch('gender')
  const selectedActivity = watch('activity_level')

  return (
    <form onSubmit={handleSubmit(onNext)} className="space-y-4">
      <div className="text-center space-y-0.5">
        <h2 className="text-lg font-bold text-foreground">About you</h2>
        <p className="text-xs text-muted-foreground">Used to calculate your personalised calorie target</p>
      </div>

      {/* Height + Weight */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Height</label>
          <div className="relative">
            <input
              type="number"
              placeholder="175"
              {...register('height_cm', { valueAsNumber: true })}
              className="w-full bg-muted border border-border rounded-xl px-3 py-2.5 text-sm text-foreground pr-10 focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">cm</span>
          </div>
          {errors.height_cm && <p className="text-xs text-destructive">{errors.height_cm.message}</p>}
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Weight</label>
          <div className="relative">
            <input
              type="number"
              placeholder="70"
              {...register('weight_kg', { valueAsNumber: true })}
              className="w-full bg-muted border border-border rounded-xl px-3 py-2.5 text-sm text-foreground pr-10 focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">kg</span>
          </div>
          {errors.weight_kg && <p className="text-xs text-destructive">{errors.weight_kg.message}</p>}
        </div>
      </div>

      {/* DOB */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Date of birth</label>
        <input
          type="date"
          max={new Date().toISOString().split('T')[0]}
          {...register('dob')}
          className="w-full bg-muted border border-border rounded-xl px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
        {errors.dob && <p className="text-xs text-destructive">{errors.dob.message}</p>}
      </div>

      {/* Gender pills */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Gender</label>
        <div className="flex flex-wrap gap-2">
          {GENDERS.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              onClick={() => setValue('gender', value, { shouldValidate: true })}
              className={cn(
                'px-4 py-1.5 rounded-full text-sm font-medium border transition-all',
                selectedGender === value
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-muted text-muted-foreground border-border hover:border-primary/50',
              )}
            >
              {label}
            </button>
          ))}
        </div>
        {errors.gender && <p className="text-xs text-destructive">Please select a gender</p>}
      </div>

      {/* Activity level cards */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Activity level</label>
        <div className="grid grid-cols-1 gap-1.5">
          {ACTIVITY_LEVELS.map(({ value, label, desc, icon }) => (
            <button
              key={value}
              type="button"
              onClick={() => setValue('activity_level', value, { shouldValidate: true })}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-xl border text-left transition-all',
                selectedActivity === value
                  ? 'bg-primary/10 border-primary'
                  : 'bg-muted border-border hover:border-primary/40',
              )}
            >
              <span className="text-lg shrink-0">{icon}</span>
              <span className={cn('text-sm font-medium flex-1', selectedActivity === value ? 'text-foreground' : 'text-foreground/80')}>
                {label}
              </span>
              <span className="text-xs text-muted-foreground">{desc}</span>
            </button>
          ))}
        </div>
      </div>

      <button
        type="submit"
        className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:opacity-90 active:scale-[0.98] transition-all"
      >
        Continue →
      </button>

      <button type="button" onClick={onSkip} className="w-full text-center text-xs text-muted-foreground hover:text-foreground transition-colors">
        Skip for now
      </button>
    </form>
  )
}
