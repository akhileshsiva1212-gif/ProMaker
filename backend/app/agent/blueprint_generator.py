"""Generate Product Evolution Blueprint from per-change analyses."""

from __future__ import annotations

from app.memory.schema import Blueprint, ChangeAnalysis, Verdict


def generate_blueprint(analyses: list[ChangeAnalysis]) -> Blueprint:
    bp = Blueprint()
    for a in analyses:
        label = a.change
        if a.verdict == Verdict.KEEP:
            bp.keep.append(label)
        elif a.verdict == Verdict.IMPROVE:
            bp.improve.append(label)
        elif a.verdict == Verdict.RETIRE:
            bp.retire.append(label)
        elif a.verdict == Verdict.REINVENT:
            bp.reinvent.append(label)
        elif a.verdict == Verdict.INTRODUCE:
            bp.introduce.append(label)

        if a.historical_warning and a.historical_warning_detail:
            bp.historical_warnings.append(f"{a.change}: {a.historical_warning_detail}")
        if a.habit_collision and a.habit_risk_detail:
            bp.habit_risks.append(f"{a.change}: {a.habit_risk_detail}")

        # Migration notes derived from verdicts
        if a.verdict == Verdict.REINVENT:
            bp.migration_considerations.append(
                f"For «{a.change}»: plan a clean break from the previous approach; do not ship a cosmetic variant of the failed design."
            )
        if a.habit_collision:
            bp.migration_considerations.append(
                f"For «{a.change}»: provide a transition path that keeps the primary workflow discoverable during rollout."
            )

    return bp