"""
Macro split strategies.

Each strategy takes a calorie target, body weight, and goal type,
and returns a full set of macro targets (protein / carbs / fat / fibre).

Strategies differ in how they distribute calories across macros — e.g.
standard balanced split vs high-protein vs low-carb (keto-style).
"""

from abc import ABC, abstractmethod

from app.schemas.goal import MacroSuggestion

MIN_LOSE_KCAL   = 1_200   # hard floor for safety
CALORIE_DEFICIT = 500     # kcal below TDEE for lose
CALORIE_SURPLUS = 300     # kcal above TDEE for gain

FIBRE_PER_1000_KCAL = 14  # DRI guideline: ~14 g per 1 000 kcal


def _fibre(calories: int) -> int:
    return round(calories / 1000 * FIBRE_PER_1000_KCAL)


class MacroStrategy(ABC):
    @abstractmethod
    def calories_for(self, tdee: int, goal_type: str) -> int:
        """Adjust TDEE based on goal type."""
        ...

    @abstractmethod
    def macros_for(self, calories: int, weight_kg: float, goal_type: str) -> MacroSuggestion:
        """Return a full macro suggestion for the given calorie target."""
        ...

    def suggest(self, tdee: int, weight_kg: float, goal_type: str) -> MacroSuggestion:
        calories = self.calories_for(tdee, goal_type)
        return self.macros_for(calories, weight_kg, goal_type)


class StandardMacroStrategy(MacroStrategy):
    """
    Balanced macro split.
    - Protein: 1.8 g/kg (lose/maintain) or 2.2 g/kg (gain)
    - Fat: 0.9 g/kg baseline
    - Carbs: remaining calories after protein + fat
    """

    def calories_for(self, tdee: int, goal_type: str) -> int:
        if goal_type == "lose":
            return max(MIN_LOSE_KCAL, tdee - CALORIE_DEFICIT)
        if goal_type == "gain":
            return tdee + CALORIE_SURPLUS
        return tdee

    def macros_for(self, calories: int, weight_kg: float, goal_type: str) -> MacroSuggestion:
        protein_g = round(weight_kg * (2.2 if goal_type == "gain" else 1.8))
        fat_g     = round(weight_kg * 0.9)
        remaining = calories - protein_g * 4 - fat_g * 9
        carbs_g   = max(50, round(remaining / 4))
        return MacroSuggestion(
            daily_calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            fibre_g=_fibre(calories),
        )


class HighProteinMacroStrategy(MacroStrategy):
    """
    High-protein split — suitable for muscle gain / body recomposition.
    - Protein: 2.5 g/kg (lose/maintain) or 3.0 g/kg (gain)
    - Fat: 0.8 g/kg
    - Carbs: remainder
    """

    def calories_for(self, tdee: int, goal_type: str) -> int:
        if goal_type == "lose":
            return max(MIN_LOSE_KCAL, tdee - CALORIE_DEFICIT)
        if goal_type == "gain":
            return tdee + CALORIE_SURPLUS
        return tdee

    def macros_for(self, calories: int, weight_kg: float, goal_type: str) -> MacroSuggestion:
        protein_g = round(weight_kg * (3.0 if goal_type == "gain" else 2.5))
        fat_g     = round(weight_kg * 0.8)
        remaining = calories - protein_g * 4 - fat_g * 9
        carbs_g   = max(30, round(remaining / 4))
        return MacroSuggestion(
            daily_calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            fibre_g=_fibre(calories),
        )


class LowCarbMacroStrategy(MacroStrategy):
    """
    Low-carb split (moderate keto-adjacent).
    - Carbs: capped at 100 g/day
    - Protein: 2.0 g/kg
    - Fat: fills the remainder
    """

    def calories_for(self, tdee: int, goal_type: str) -> int:
        if goal_type == "lose":
            return max(MIN_LOSE_KCAL, tdee - CALORIE_DEFICIT)
        if goal_type == "gain":
            return tdee + CALORIE_SURPLUS
        return tdee

    def macros_for(self, calories: int, weight_kg: float, goal_type: str) -> MacroSuggestion:
        protein_g = round(weight_kg * 2.0)
        carbs_g   = 100
        remaining = calories - protein_g * 4 - carbs_g * 4
        fat_g     = max(30, round(remaining / 9))
        return MacroSuggestion(
            daily_calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            fibre_g=_fibre(calories),
        )


# Default — used by goal_service unless overridden
DEFAULT_MACRO_STRATEGY: MacroStrategy = StandardMacroStrategy()
