import logo from '@/assets/claorieQ.svg'

interface Props {
  name: string
  onNext: () => void
}

export default function StepWelcome({ name, onNext }: Props) {
  return (
    <div className="flex flex-col items-center text-center gap-8">
      <div className="relative">
        <div className="w-24 h-24 rounded-3xl bg-primary/10 border border-primary/20 flex items-center justify-center">
          <img src={logo} alt="CalorieQ" className="w-14 h-14" />
        </div>
        <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-primary animate-pulse" />
      </div>

      <div className="space-y-3">
        <h1 className="text-3xl font-bold text-foreground">
          Welcome, {name}! 👋
        </h1>
        <p className="text-muted-foreground text-base leading-relaxed max-w-xs">
          Let's personalise your dashboard in two quick steps so the calorie ring actually means something.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3 w-full max-w-xs text-xs text-muted-foreground">
        {[
          { icon: '⚡', label: '2 min setup' },
          { icon: '🎯', label: 'Personalised goals' },
          { icon: '📊', label: 'Smart insights' },
        ].map(({ icon, label }) => (
          <div key={label} className="bg-muted/50 rounded-xl p-3 space-y-1">
            <div className="text-xl">{icon}</div>
            <div>{label}</div>
          </div>
        ))}
      </div>

      <button
        onClick={onNext}
        className="w-full max-w-xs py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:opacity-90 active:scale-[0.98] transition-all"
      >
        Get started →
      </button>
    </div>
  )
}
