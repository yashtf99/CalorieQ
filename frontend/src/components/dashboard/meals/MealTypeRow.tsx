import { ChevronDown, Plus } from 'lucide-react'
import { useState } from 'react'
import type { MealLogOut, MealType } from '@/types/meals'
import MealEntryRow from './MealEntryRow'

interface Props {
  type: MealType
  entries: MealLogOut[]
  date: string
  onAdd: (type: MealType) => void
}

const mealMeta: Record<MealType, { emoji: string; label: string }> = {
  breakfast: { emoji: '🍳', label: 'Breakfast' },
  lunch: { emoji: '🍛', label: 'Lunch' },
  snacks: { emoji: '🍎', label: 'Snacks' },
  dinner: { emoji: '🍲', label: 'Dinner' },
}

export default function MealTypeRow({ type, entries, date, onAdd }: Props) {
  const [isExpanded, setIsExpanded] = useState(false)
  const meta = mealMeta[type]
  const totalKcal = entries.reduce((sum, e) => sum + (e.energy_kcal ?? 0), 0)

  return (
    <div className="border-b border-border last:border-0">
      <button
        onClick={() => entries.length > 0 && setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-3 py-3 hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <span className="text-lg">{meta.emoji}</span>
          <span className="font-medium">{meta.label}</span>
          {!isExpanded && entries.length > 0 && (
            <span className="text-sm text-muted-foreground">
              {entries.length} items • {Math.round(totalKcal)} kcal
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onAdd(type)
            }}
            className="p-1 hover:bg-muted rounded transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
          {entries.length > 0 && (
            <ChevronDown
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="bg-muted/30">
          {entries.length === 0 ? (
            <p className="px-3 py-4 text-sm text-muted-foreground text-center">No entries</p>
          ) : (
            entries.map((entry) => (
              <MealEntryRow key={entry.id} entry={entry} date={date} />
            ))
          )}
        </div>
      )}
    </div>
  )
}
