import { format, isToday, parseISO } from 'date-fns'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useDateStore } from '@/store/dateStore'

export default function DateSelector() {
  const { selectedDate, goToPrev, goToNext } = useDateStore()
  const date = parseISO(selectedDate)
  const today = isToday(date)

  return (
    <div className="flex flex-col items-end gap-0.5">
      {today && (
        <span className="text-xs font-medium text-primary uppercase tracking-widest">
          Today
        </span>
      )}
      <div className="flex items-center gap-1">
        <button
          onClick={goToPrev}
          className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
          aria-label="Previous day"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="text-sm font-medium text-foreground min-w-[110px] text-center">
          {format(date, 'EEE, d MMM')}
        </span>
        <button
          onClick={goToNext}
          disabled={today}
          className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Next day"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}
