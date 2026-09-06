import { AlertCircle, X } from 'lucide-react'
import { useState } from 'react'

interface Props {
  message: string
  onRetry?: () => void
  onDismiss?: () => void
}

export default function ErrorBanner({ message, onRetry, onDismiss }: Props) {
  const [isVisible, setIsVisible] = useState(true)

  if (!isVisible) return null

  const handleDismiss = () => {
    setIsVisible(false)
    onDismiss?.()
  }

  return (
    <div className="flex items-center gap-3 bg-destructive/10 border border-destructive/20 rounded-xl p-4 text-sm text-destructive">
      <AlertCircle size={16} className="flex-shrink-0" />
      <span className="flex-1">{message}</span>
      <div className="flex items-center gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-xs font-medium hover:underline"
          >
            Retry
          </button>
        )}
        <button
          onClick={handleDismiss}
          className="p-1 hover:bg-destructive/20 rounded transition-colors"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  )
}
