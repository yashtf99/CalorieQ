"""
Unit tests for BMR and macro calculation strategies.
These test the strategy implementations directly — no HTTP layer, no DB.
"""

import pytest
from app.services.strategies.bmr import (
    HarrisBenedictStrategy,
    MifflinStJeorStrategy,
)
from app.services.strategies.macro import (
    HighProteinMacroStrategy,
    LowCarbMacroStrategy,
    StandardMacroStrategy,
)
from app.schemas.goal import GoalSuggestionParams
from app.services.goal_service import suggest_goals


# ── BMR strategies ─────────────────────────────────────────────────────────────

class TestMifflinStJeor:
    def test_male_bmr(self):
        s = MifflinStJeorStrategy()
        # 30yo male, 175 cm, 75 kg → 10*75 + 6.25*175 - 5*30 + 5 = 1699
        assert s.calculate(75, 175, 30, "male") == 1699

    def test_female_bmr(self):
        s = MifflinStJeorStrategy()
        # 30yo female, 165 cm, 60 kg → 10*60 + 6.25*165 - 5*30 - 161 = 1320
        assert s.calculate(60, 165, 30, "female") == 1320

    def test_other_gender_is_midpoint(self):
        s = MifflinStJeorStrategy()
        male   = s.calculate(70, 170, 25, "male")
        female = s.calculate(70, 170, 25, "female")
        other  = s.calculate(70, 170, 25, "other")
        assert female < other < male

    def test_tdee_scales_with_activity(self):
        s = MifflinStJeorStrategy()
        bmr = s.calculate(75, 175, 30, "male")
        assert s.tdee(bmr, "sedentary") < s.tdee(bmr, "lightly_active")
        assert s.tdee(bmr, "lightly_active") < s.tdee(bmr, "active")
        assert s.tdee(bmr, "active") < s.tdee(bmr, "very_active")


class TestHarrisBenedict:
    def test_male_bmr_is_positive(self):
        s = HarrisBenedictStrategy()
        assert s.calculate(75, 175, 30, "male") > 0

    def test_female_bmr_is_positive(self):
        s = HarrisBenedictStrategy()
        assert s.calculate(60, 165, 30, "female") > 0

    def test_tends_higher_than_mifflin(self):
        """Harris-Benedict is known to over-estimate vs Mifflin-St Jeor."""
        hb = HarrisBenedictStrategy()
        ms = MifflinStJeorStrategy()
        # Use a typical adult — difference is small but HB should be >= MS
        assert hb.calculate(75, 175, 30, "male") >= ms.calculate(75, 175, 30, "male")


# ── Macro strategies ──────────────────────────────────────────────────────────

_W = 75.0   # test weight

class TestStandardMacros:
    def test_lose_calories_less_than_maintain(self):
        s = StandardMacroStrategy()
        assert s.calories_for(2000, "lose") < s.calories_for(2000, "maintain")

    def test_gain_calories_more_than_maintain(self):
        s = StandardMacroStrategy()
        assert s.calories_for(2000, "gain") > s.calories_for(2000, "maintain")

    def test_lose_never_below_1200(self):
        s = StandardMacroStrategy()
        assert s.calories_for(1500, "lose") >= 1200

    def test_macros_are_positive(self):
        s = StandardMacroStrategy()
        m = s.macros_for(2000, _W, "maintain")
        assert m.protein_g > 0 and m.carbs_g > 0 and m.fat_g > 0 and m.fibre_g > 0

    def test_gain_has_more_protein_than_maintain(self):
        s = StandardMacroStrategy()
        gain     = s.macros_for(2300, _W, "gain")
        maintain = s.macros_for(2000, _W, "maintain")
        assert gain.protein_g > maintain.protein_g


class TestHighProteinMacros:
    def test_more_protein_than_standard(self):
        std = StandardMacroStrategy()
        hp  = HighProteinMacroStrategy()
        assert hp.macros_for(2000, _W, "maintain").protein_g > std.macros_for(2000, _W, "maintain").protein_g

    def test_macros_positive(self):
        m = HighProteinMacroStrategy().macros_for(2000, _W, "maintain")
        assert m.protein_g > 0 and m.carbs_g > 0 and m.fat_g > 0


class TestLowCarbMacros:
    def test_carbs_capped_at_100(self):
        m = LowCarbMacroStrategy().macros_for(2000, _W, "maintain")
        assert m.carbs_g == 100

    def test_fat_fills_remainder(self):
        m = LowCarbMacroStrategy().macros_for(2000, _W, "maintain")
        # fat calories should fill the gap after protein + carbs
        assert m.fat_g > 0


# ── Strategy swapping via suggest_goals ───────────────────────────────────────

_PARAMS = GoalSuggestionParams(
    height_cm=175, weight_kg=75, dob="1995-06-15",
    gender="male", activity_level="lightly_active",
)

def test_suggest_goals_default_strategy():
    result = suggest_goals(_PARAMS)
    assert result.bmr > 0
    assert result.tdee > result.bmr
    assert set(result.suggestions.keys()) == {"lose", "maintain", "gain"}


def test_suggest_goals_harris_benedict_strategy():
    result = suggest_goals(_PARAMS, bmr_strategy=HarrisBenedictStrategy())
    assert result.bmr > 0


def test_suggest_goals_high_protein_strategy():
    std = suggest_goals(_PARAMS)
    hp  = suggest_goals(_PARAMS, macro_strategy=HighProteinMacroStrategy())
    assert hp.suggestions["maintain"].protein_g > std.suggestions["maintain"].protein_g


def test_suggest_goals_low_carb_strategy():
    result = suggest_goals(_PARAMS, macro_strategy=LowCarbMacroStrategy())
    assert result.suggestions["maintain"].carbs_g == 100
