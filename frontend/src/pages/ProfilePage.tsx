import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { useAuthStore } from '@/store/authStore'

const profileSchema = z.object({
  dob: z.string().optional(),
  gender: z.enum(['male', 'female', 'other']).optional(),
  height_cm: z.number().int().min(100).max(250).optional(),
  activity_level: z.enum(['sedentary', 'light', 'moderate', 'active', 'very_active']).optional(),
})

const goalsSchema = z.object({
  goal_type: z.enum(['lose', 'maintain', 'gain']),
  daily_calories: z.number().int().gt(0).lt(15000).optional(),
  protein_g: z.number().gte(0).lt(1000).optional(),
  carbs_g: z.number().gte(0).lt(1000).optional(),
  fat_g: z.number().gte(0).lt(500).optional(),
  fibre_g: z.number().gte(0).lt(500).optional(),
})

type ProfileFormData = z.infer<typeof profileSchema>
type GoalsFormData = z.infer<typeof goalsSchema>

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user)
  const [displayName, setDisplayName] = useState(user?.display_name ?? '')
  const [isEditingName, setIsEditingName] = useState(false)
  const [isLoadingProfile, setIsLoadingProfile] = useState(false)
  const [isLoadingGoals, setIsLoadingGoals] = useState(false)

  const profileForm = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      dob: '',
      gender: undefined,
      height_cm: undefined,
      activity_level: 'moderate',
    },
  })

  const goalsForm = useForm<GoalsFormData>({
    resolver: zodResolver(goalsSchema),
    defaultValues: {
      goal_type: 'maintain',
      daily_calories: 2000,
      protein_g: 150,
      carbs_g: 225,
      fat_g: 65,
      fibre_g: 25,
    },
  })

  const onProfileSubmit = async (data: ProfileFormData) => {
    setIsLoadingProfile(true)
    try {
      // TODO: Call API to update profile
      console.log('Profile update:', data)
      toast.success('Profile updated successfully')
    } catch (error) {
      toast.error('Failed to update profile')
    } finally {
      setIsLoadingProfile(false)
    }
  }

  const onGoalsSubmit = async (data: GoalsFormData) => {
    setIsLoadingGoals(true)
    try {
      // TODO: Call API to create/update goal
      console.log('Goal update:', data)
      toast.success('Goals updated successfully')
    } catch (error) {
      toast.error('Failed to update goals')
    } finally {
      setIsLoadingGoals(false)
    }
  }

  const onNameSave = async () => {
    if (!displayName.trim()) {
      toast.error('Name cannot be empty')
      return
    }
    try {
      // TODO: Call API to update display name
      console.log('Name update:', displayName)
      toast.success('Name updated successfully')
      setIsEditingName(false)
    } catch (error) {
      toast.error('Failed to update name')
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Profile</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Manage your personal information and fitness goals</p>
      </div>

      {/* Display Name */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Display Name</h2>
        <div className="flex items-center gap-3">
          {isEditingName ? (
            <>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="flex-1 px-3 py-2 border border-border rounded-lg"
                placeholder="Your name"
              />
              <button
                onClick={onNameSave}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 text-sm font-medium"
              >
                Save
              </button>
              <button
                onClick={() => {
                  setIsEditingName(false)
                  setDisplayName(user?.display_name ?? '')
                }}
                className="px-4 py-2 bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 text-sm font-medium"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <p className="flex-1 text-foreground">{displayName}</p>
              <button
                onClick={() => setIsEditingName(true)}
                className="px-4 py-2 bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 text-sm font-medium"
              >
                Edit
              </button>
            </>
          )}
        </div>
      </div>

      {/* Personal Info */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Personal Information</h2>
        <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Date of Birth</label>
              <input
                type="date"
                {...profileForm.register('dob')}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Gender</label>
              <select
                {...profileForm.register('gender')}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
              >
                <option value="">Select gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Height (cm)</label>
              <input
                type="number"
                step="0.1"
                {...profileForm.register('height_cm', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
                placeholder="170"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Activity Level</label>
              <select
                {...profileForm.register('activity_level')}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
              >
                <option value="sedentary">Sedentary</option>
                <option value="light">Lightly Active</option>
                <option value="moderate">Moderately Active</option>
                <option value="active">Very Active</option>
                <option value="very_active">Extremely Active</option>
              </select>
            </div>

          </div>

          <button
            type="submit"
            disabled={isLoadingProfile}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 text-sm font-medium"
          >
            {isLoadingProfile ? 'Saving...' : 'Save Profile'}
          </button>
        </form>
      </div>

      {/* Goals */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Fitness Goals</h2>
        <form onSubmit={goalsForm.handleSubmit(onGoalsSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Goal Type</label>
            <div className="flex gap-4">
              {(['lose', 'maintain', 'gain'] as const).map((type) => (
                <label key={type} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    value={type}
                    {...goalsForm.register('goal_type')}
                    className="w-4 h-4"
                  />
                  <span className="text-sm capitalize">{type}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Daily Calories</label>
              <input
                type="number"
                {...goalsForm.register('daily_calories', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
                placeholder="2000"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Protein (g)</label>
              <input
                type="number"
                step="0.1"
                {...goalsForm.register('protein_g', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
                placeholder="150"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Carbs (g)</label>
              <input
                type="number"
                step="0.1"
                {...goalsForm.register('carbs_g', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
                placeholder="225"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Fat (g)</label>
              <input
                type="number"
                step="0.1"
                {...goalsForm.register('fat_g', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
                placeholder="65"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Fibre (g)</label>
              <input
                type="number"
                step="0.1"
                {...goalsForm.register('fibre_g', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm"
                placeholder="25"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoadingGoals}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 text-sm font-medium"
          >
            {isLoadingGoals ? 'Saving...' : 'Save Goals'}
          </button>
        </form>
      </div>
    </div>
  )
}
