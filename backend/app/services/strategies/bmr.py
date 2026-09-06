"""
BMR calculation strategies.

Each strategy implements the same interface: given physical stats,
return a basal metabolic rate in kcal/day.

Activity multipliers are shared across all BMR strategies — they are
a property of the TDEE calculation, not the BMR equation itself.
"""

from abc import ABC, abstractmethod


ACTIVITY_MULTIPLIER: dict[str, float] = {
    "sedentary":      1.2,
    "lightly_active": 1.375,
    "active":         1.55,
    "very_active":    1.725,
}


class BMRStrategy(ABC):
    @abstractmethod
    def calculate(self, weight_kg: float, height_cm: float, age: int, gender: str) -> int:
        """Return BMR in kcal/day."""
        ...

    def tdee(self, bmr: int, activity_level: str) -> int:
        return round(bmr * ACTIVITY_MULTIPLIER[activity_level])


class MifflinStJeorStrategy(BMRStrategy):
    """
    Mifflin-St Jeor (1990) — current gold standard for general populations.
    Most widely used in clinical and consumer nutrition tools.
    """

    def calculate(self, weight_kg: float, height_cm: float, age: int, gender: str) -> int:
        base = 10 * weight_kg + 6.25 * height_cm - 5 * age
        if gender == "male":
            return round(base + 5)
        if gender == "female":
            return round(base - 161)
        return round(base - 78)   # other / prefer_not_to_say → midpoint of M and F constants


class HarrisBenedictStrategy(BMRStrategy):
    """
    Harris-Benedict (revised 1984, Roza & Shizgal).
    Older formula; tends to over-estimate BMR slightly vs Mifflin-St Jeor.
    Kept here as an alternative / for comparison.
    """

    def calculate(self, weight_kg: float, height_cm: float, age: int, gender: str) -> int:
        if gender == "male":
            return round(88.362 + 13.397 * weight_kg + 4.799 * height_cm - 5.677 * age)
        if gender == "female":
            return round(447.593 + 9.247 * weight_kg + 3.098 * height_cm - 4.330 * age)
        male   = 88.362 + 13.397 * weight_kg + 4.799 * height_cm - 5.677 * age
        female = 447.593 + 9.247 * weight_kg + 3.098 * height_cm - 4.330 * age
        return round((male + female) / 2)


# Default — used by goal_service unless overridden
DEFAULT_BMR_STRATEGY: BMRStrategy = MifflinStJeorStrategy()
