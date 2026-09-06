import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { useGoalSuggestion, useCreateGoal } from '@/api/goals'
import { usePatchProfile } from '@/api/users'
import type { GoalSuggestionParams } from '@/types/goals'
import StepWelcome from './steps/StepWelcome'
import StepProfile, { type ProfileFormValues } from './steps/StepProfile'
import StepGoal, { type GoalFormValues } from './steps/StepGoal'
import StepDone from './steps/StepDone'

const STEPS = ['welcome', 'profile', 'goal', 'done'] as const
type Step = typeof STEPS[number]

interface Props {
  userName: string
  onFinish: () => void
}

const STEP_LABELS = ['Welcome', 'About you', 'Your goal', 'Done']

function ProgressDots({ current }: { current: number }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {STEP_LABELS.slice(1).map((label, i) => (
        <div key={label} className="flex items-center gap-2">
          {i > 0 && (
            <div className={`h-px w-8 transition-colors ${current > i ? 'bg-primary' : 'bg-border'}`} />
          )}
          <div className={`flex items-center gap-1.5 transition-all`}>
            <div
              className={`w-2 h-2 rounded-full transition-all ${
                current > i + 1
                  ? 'bg-primary'
                  : current === i + 1
                  ? 'bg-primary ring-4 ring-primary/20'
                  : 'bg-border'
              }`}
            />
            <span className={`text-xs transition-colors hidden sm:block ${current === i + 1 ? 'text-foreground' : 'text-muted-foreground'}`}>
              {label}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function OnboardingWizard({ userName, onFinish }: Props) {
  const [step, setStep] = useState<Step>('welcome')
  const [profileData, setProfileData] = useState<ProfileFormValues | null>(null)
  const [completedGoal, setCompletedGoal] = useState<GoalFormValues | null>(null)

  const patchProfile = usePatchProfile()
  const createGoal   = useCreateGoal()
  const queryClient  = useQueryClient()

  // Build suggestion params only after profile step is complete
  const suggestionParams: GoalSuggestionParams | null = profileData
    ? {
        height_cm:      profileData.height_cm,
        weight_kg:      profileData.weight_kg,
        dob:            profileData.dob,
        gender:         profileData.gender,
        activity_level: profileData.activity_level,
      }
    : null

  const { data: suggestion, isLoading: isSuggestionLoading } = useGoalSuggestion(suggestionParams)

  const currentStepIndex = STEPS.indexOf(step)

  async function handleProfileNext(data: ProfileFormValues) {
    setProfileData(data)
    try {
      await patchProfile.mutateAsync({
        height_cm:           data.height_cm,
        current_weight_kg:   data.weight_kg,
        dob:                 data.dob,
        gender:              data.gender,
        activity_level:      data.activity_level,
      })
      setStep('goal')
    } catch {
      // toast already fired in usePatchProfile; stay on this step
    }
  }

  async function handleGoalDone(data: GoalFormValues) {
    try {
      await createGoal.mutateAsync({
        goal_type:      data.goal_type,
        daily_calories: data.daily_calories,
        protein_g:      data.protein_g,
        carbs_g:        data.carbs_g,
        fat_g:          data.fat_g,
        fibre_g:        data.fibre_g,
      })
      setCompletedGoal(data)
      setStep('done')
    } catch {
      // toast already fired in useCreateGoal
    }
  }

  function handleFinish() {
    // Invalidate dashboard queries so ring + bars refresh with real goal
    queryClient.invalidateQueries({ queryKey: ['daily-summary'] })
    queryClient.invalidateQueries({ queryKey: ['weekly-report'] })
    onFinish()
  }

  function handleSkip() {
    toast('You can set your goals any time from Profile.')
    onFinish()
  }

  return (
    // Full-screen overlay
    <div className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-card border border-border rounded-2xl shadow-2xl flex flex-col max-h-[calc(100svh-2rem)]">
        {step !== 'welcome' && step !== 'done' && (
          <div className="px-7 pt-6 shrink-0">
            <ProgressDots current={currentStepIndex} />
          </div>
        )}
        <div className="overflow-y-auto px-7 py-6 flex-1">

        {step === 'welcome' && (
          <StepWelcome name={userName} onNext={() => setStep('profile')} />
        )}

        {step === 'profile' && (
          <StepProfile
            defaultValues={profileData ?? undefined}
            onNext={handleProfileNext}
            onSkip={handleSkip}
          />
        )}

        {step === 'goal' && (
          <StepGoal
            suggestion={suggestion}
            isSuggestionLoading={isSuggestionLoading}
            onDone={handleGoalDone}
            onBack={() => setStep('profile')}
          />
        )}

        {step === 'done' && completedGoal && (
          <StepDone goal={completedGoal} onFinish={handleFinish} />
        )}
        </div>
      </div>
    </div>
  )
}
