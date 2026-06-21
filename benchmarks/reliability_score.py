"""Autonomic Reliability Score (ARS) — composite metric for model evaluation.

Combines three signals into a single 0–100 score:
  - pass@1 (functional correctness): 40% weight
  - keyword accuracy (convention adherence): 30% weight
  - sandbox pass rate (execution safety): 30% weight

This answers: "Can a 1.5B model + Autonomic brain achieve the same
reliability as a raw frontier model?"

Usage:
    from reliability_score import compute_ars

    score = compute_ars(
        pass_at_1=0.65,        # 65% of problems pass
        keyword_accuracy=0.82, # 82% keyword hit rate
        sandbox_pass_rate=0.70 # 70% of generated code runs
    )
    print(f"ARS: {score}")  # e.g., ARS: 72.6
"""

from dataclasses import dataclass


# Component weights (must sum to 1.0)
WEIGHT_PASS_AT_1 = 0.40
WEIGHT_KEYWORD_ACCURACY = 0.30
WEIGHT_SANDBOX_PASS = 0.30


@dataclass(frozen=True)
class ARSResult:
    """Autonomic Reliability Score result."""
    total_score: float
    pass_at_1_score: float
    keyword_accuracy_score: float
    sandbox_pass_score: float
    grade: str


def _grade(score: float) -> str:
    """Map a 0-100 score to a letter grade."""
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def compute_ars(
    pass_at_1: float,
    keyword_accuracy: float,
    sandbox_pass_rate: float,
) -> ARSResult:
    """Compute the Autonomic Reliability Score.

    Args:
        pass_at_1: Fraction of HumanEval problems passing (0.0 - 1.0)
        keyword_accuracy: Fraction of expected keywords found (0.0 - 1.0)
        sandbox_pass_rate: Fraction of generated code running without error (0.0 - 1.0)

    Returns:
        ARSResult with total score (0-100) and per-component breakdown.
    """
    # Clamp inputs to [0, 1]
    p = max(0.0, min(1.0, pass_at_1))
    k = max(0.0, min(1.0, keyword_accuracy))
    s = max(0.0, min(1.0, sandbox_pass_rate))

    p_score = p * 100 * WEIGHT_PASS_AT_1
    k_score = k * 100 * WEIGHT_KEYWORD_ACCURACY
    s_score = s * 100 * WEIGHT_SANDBOX_PASS

    total = round(p_score + k_score + s_score, 1)

    return ARSResult(
        total_score=total,
        pass_at_1_score=round(p_score, 1),
        keyword_accuracy_score=round(k_score, 1),
        sandbox_pass_score=round(s_score, 1),
        grade=_grade(total),
    )


def compare_models(
    model_a_name: str, model_a_ars: ARSResult,
    model_b_name: str, model_b_ars: ARSResult,
) -> str:
    """Generate a human-readable comparison between two model configurations."""
    delta = model_a_ars.total_score - model_b_ars.total_score
    direction = "higher" if delta > 0 else "lower"
    abs_delta = abs(delta)

    lines = [
        f"## Reliability Comparison",
        f"",
        f"| Metric | {model_a_name} | {model_b_name} | Delta |",
        f"|---|---|---|---|",
        f"| **ARS (total)** | **{model_a_ars.total_score}** ({model_a_ars.grade}) "
        f"| **{model_b_ars.total_score}** ({model_b_ars.grade}) "
        f"| {delta:+.1f} |",
        f"| pass@1 (40%) | {model_a_ars.pass_at_1_score} | {model_b_ars.pass_at_1_score} "
        f"| {model_a_ars.pass_at_1_score - model_b_ars.pass_at_1_score:+.1f} |",
        f"| Keywords (30%) | {model_a_ars.keyword_accuracy_score} | {model_b_ars.keyword_accuracy_score} "
        f"| {model_a_ars.keyword_accuracy_score - model_b_ars.keyword_accuracy_score:+.1f} |",
        f"| Sandbox (30%) | {model_a_ars.sandbox_pass_score} | {model_b_ars.sandbox_pass_score} "
        f"| {model_a_ars.sandbox_pass_score - model_b_ars.sandbox_pass_score:+.1f} |",
        f"",
    ]

    if abs_delta < 5:
        lines.append(f"> **{model_a_name}** achieves comparable reliability to "
                     f"**{model_b_name}** (within {abs_delta:.1f} ARS points).")
    else:
        lines.append(f"> **{model_a_name}** scores {abs_delta:.1f} ARS points "
                     f"{direction} than **{model_b_name}**.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example: compare a 1.5B model + brain vs GPT-4 raw
    small_enhanced = compute_ars(
        pass_at_1=0.55,
        keyword_accuracy=0.82,
        sandbox_pass_rate=0.60,
    )
    frontier_raw = compute_ars(
        pass_at_1=0.86,
        keyword_accuracy=0.65,
        sandbox_pass_rate=0.80,
    )

    print(f"Qwen 1.5B + Brain ARS: {small_enhanced.total_score} ({small_enhanced.grade})")
    print(f"GPT-4 raw ARS:         {frontier_raw.total_score} ({frontier_raw.grade})")
    print()
    print(compare_models(
        "Qwen-1.5B + Autonomic", small_enhanced,
        "GPT-4 (raw)", frontier_raw,
    ))
