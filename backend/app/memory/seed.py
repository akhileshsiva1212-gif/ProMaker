"""
Seed data for FlowSync — a believable B2B SaaS product.
Coherent product decision history covering onboarding, checkout, search, and recommendations.
"""

from datetime import datetime, timedelta

from app.memory.schema import MemoryType, MemoryUnit, ProductVersion


def build_seed_memories() -> list[MemoryUnit]:
    base = datetime(2024, 3, 1)
    memories: list[MemoryUnit] = []

    def m(
        id: str,
        mtype: MemoryType,
        title: str,
        content: str,
        *,
        problem: str | None = None,
        decision: str | None = None,
        experiment: str | None = None,
        customer_reaction: str | None = None,
        outcome: str | None = None,
        lesson: str | None = None,
        feature_area: str | None = None,
        tags: list[str] | None = None,
        metrics: dict | None = None,
        days: int = 0,
        version: ProductVersion = ProductVersion.V1,
        related: list[str] | None = None,
    ) -> MemoryUnit:
        return MemoryUnit(
            id=id,
            memory_type=mtype,
            product_version=version,
            title=title,
            content=content,
            problem=problem,
            decision=decision,
            experiment=experiment,
            customer_reaction=customer_reaction,
            outcome=outcome,
            lesson=lesson,
            feature_area=feature_area,
            tags=tags or [],
            metrics=metrics or {},
            related_ids=related or [],
            created_at=base + timedelta(days=days),
            source="seed",
        )

    # ── ONBOARDING STORY ──────────────────────────────────────────────
    memories.append(
        m(
            "M-001",
            MemoryType.FEEDBACK,
            "Users abandon onboarding mid-flow",
            "Multiple customer interviews and support tickets report that new users drop off during the initial setup wizard.",
            feature_area="onboarding",
            tags=["onboarding", "abandonment", "activation"],
            metrics={"abandonment_rate": 0.47, "started_sessions": 1240, "completed_sessions": 657},
            days=5,
        )
    )
    memories.append(
        m(
            "M-002",
            MemoryType.DECISION,
            "Add step-by-step onboarding tutorial",
            "Product decided to solve abandonment by adding a detailed instructional tutorial.",
            problem="Users were abandoning onboarding at a high rate (47%).",
            decision="Add a step-by-step onboarding tutorial with detailed instructions on every screen.",
            feature_area="onboarding",
            tags=["onboarding", "tutorial", "decision"],
            days=12,
            related=["M-001"],
        )
    )
    memories.append(
        m(
            "M-003",
            MemoryType.EXPERIMENT,
            "Detailed instructional onboarding experiment",
            "Shipped a multi-step tutorial with tooltips, checklist, and explanatory copy on every onboarding screen.",
            experiment="Introduced detailed onboarding instructions across 8 screens with mandatory checklist.",
            feature_area="onboarding",
            tags=["onboarding", "experiment", "A/B"],
            metrics={"variant": "detailed_tutorial", "exposure": 620},
            days=25,
            related=["M-002"],
        )
    )
    memories.append(
        m(
            "M-004",
            MemoryType.FEEDBACK,
            "Users found onboarding too long and instructional",
            "Post-experiment interviews: users said the tutorial felt like reading a manual. Many skipped or closed early.",
            customer_reaction="Users found onboarding too long and overly instructional. Several described it as 'lecture-like'.",
            feature_area="onboarding",
            tags=["onboarding", "feedback", "friction"],
            days=40,
            related=["M-003"],
        )
    )
    memories.append(
        m(
            "M-005",
            MemoryType.OUTCOME,
            "Onboarding completion did not improve",
            "After 6 weeks the detailed tutorial showed no statistically meaningful lift in completion.",
            outcome="Completion rate did not improve meaningfully (48% vs previous 53%). Time-to-complete increased by 2.4 minutes.",
            feature_area="onboarding",
            tags=["onboarding", "outcome", "failed"],
            metrics={
                "completion_rate_before": 0.53,
                "completion_rate_after": 0.48,
                "avg_time_minutes_before": 4.1,
                "avg_time_minutes_after": 6.5,
            },
            days=55,
            related=["M-003", "M-004"],
        )
    )
    memories.append(
        m(
            "M-006",
            MemoryType.LESSON,
            "Complexity, not lack of instructions, was the problem",
            "The team concluded the root issue was product complexity, not absence of guidance.",
            lesson="The problem was complexity, not lack of instructions. Adding more instructional content increased friction without improving activation. Future onboarding work should prioritize simplification over explanation.",
            feature_area="onboarding",
            tags=["onboarding", "lesson", "complexity"],
            days=58,
            related=["M-005", "M-002"],
        )
    )

    # ── CHECKOUT / SUBSCRIPTION STORY ─────────────────────────────────
    memories.append(
        m(
            "M-010",
            MemoryType.FEEDBACK,
            "Customers value fast, low-friction checkout",
            "Sales and CS consistently report that buyers abandon when subscription checkout has too many steps or required fields.",
            feature_area="checkout",
            tags=["checkout", "friction", "conversion"],
            metrics={"checkout_abandonment": 0.22},
            days=8,
        )
    )
    memories.append(
        m(
            "M-011",
            MemoryType.DECISION,
            "Keep checkout short and single-page",
            "Product committed to a single-page, low-field checkout experience.",
            problem="Checkout abandonment was hurting conversion.",
            decision="Keep checkout short: single page, minimal required fields, no forced account creation before payment.",
            feature_area="checkout",
            tags=["checkout", "decision", "low-friction"],
            days=15,
            related=["M-010"],
        )
    )
    memories.append(
        m(
            "M-012",
            MemoryType.OUTCOME,
            "Low-friction checkout achieved strong adoption",
            "After simplifying checkout, conversion and completion improved and stayed stable.",
            outcome="Checkout completion rose to 81%. Customers repeatedly cited 'quick to start' as a reason for choosing FlowSync.",
            feature_area="checkout",
            tags=["checkout", "outcome", "success"],
            metrics={"completion_rate": 0.81, "avg_fields_filled": 4},
            days=70,
            related=["M-011"],
        )
    )
    memories.append(
        m(
            "M-013",
            MemoryType.LESSON,
            "Low-friction checkout is a core customer value",
            "Fast, simple checkout is a proven value, not merely an implementation detail.",
            lesson="Customers value low-friction checkout. Preserve the value of speed and simplicity even if the UI is redesigned. Do not re-introduce multi-step friction without strong evidence.",
            feature_area="checkout",
            tags=["checkout", "lesson", "value"],
            days=72,
            related=["M-012"],
        )
    )

    # ── SEARCH & WORKFLOW HABIT ───────────────────────────────────────
    memories.append(
        m(
            "M-020",
            MemoryType.WORKFLOW,
            "Primary workflow: Dashboard → Search → Product → Checkout",
            "The majority of successful activation sessions follow: open Dashboard → use global Search → open a Product/Project → proceed to Checkout or invite teammates.",
            feature_area="search",
            tags=["search", "workflow", "habit", "navigation"],
            metrics={"sessions_following_path": 0.68, "search_usage_rate": 0.74},
            days=20,
        )
    )
    memories.append(
        m(
            "M-021",
            MemoryType.HABIT,
            "Users are accustomed to prominent global Search",
            "Customers have formed a strong habit of relying on the always-visible top Search bar. Moving or hiding it creates orientation friction. Search is used in 74% of active sessions.",
            feature_area="search",
            tags=["search", "habit", "navigation"],
            metrics={"search_usage_rate": 0.74},
            days=30,
            related=["M-020"],
        )
    )
    memories.append(
        m(
            "M-022",
            MemoryType.FEEDBACK,
            "Users expect Search to stay discoverable",
            "When Search was temporarily less visible during a UI experiment, support tickets about 'can't find things' spiked.",
            customer_reaction="Users reported difficulty locating projects and templates when Search was less prominent.",
            feature_area="search",
            tags=["search", "feedback", "discoverability"],
            days=45,
            related=["M-021"],
        )
    )
    memories.append(
        m(
            "M-023",
            MemoryType.LESSON,
            "Major changes to Search placement create habit friction",
            "Search placement is part of learned muscle memory for the product.",
            lesson="Major changes to search placement may create habit friction. Any redesign should preserve low-friction access to search even if the visual treatment changes.",
            feature_area="search",
            tags=["search", "lesson", "habit"],
            days=50,
            related=["M-020", "M-021", "M-022"],
        )
    )

    # ── RECOMMENDATIONS / AI OPPORTUNITY ──────────────────────────────
    memories.append(
        m(
            "M-030",
            MemoryType.FEEDBACK,
            "Customers ask for smarter suggestions",
            "Several enterprise accounts requested better recommendations for templates, workflows, and next actions. Interview themes: show me what similar teams set up, suggest the next automation, I do not know which template fits us.",
            feature_area="recommendations",
            tags=["recommendations", "ai", "request", "unmet-need"],
            days=35,
        )
    )
    memories.append(
        m(
            "M-031",
            MemoryType.EXPERIMENT,
            "Rule-based recommendation banner (limited success)",
            "A simple rule-based 'Suggested for you' banner was tested.",
            experiment="Displayed static rule-based template suggestions on the dashboard for 4 weeks.",
            outcome="Click-through was modest (9%). Users wanted context-aware suggestions, not generic lists.",
            feature_area="recommendations",
            tags=["recommendations", "experiment"],
            metrics={"ctr": 0.09},
            days=60,
            related=["M-030"],
        )
    )
    memories.append(
        m(
            "M-032",
            MemoryType.LESSON,
            "Recommendation need is real; generic lists are weak",
            "There is clear unmet demand for intelligent recommendations, but naive rule-based surfaces under-delivered.",
            lesson="Customers have an unmet need for relevant recommendations. Generic or purely rule-based lists do not satisfy it. A more intelligent, context-aware approach is warranted.",
            feature_area="recommendations",
            tags=["recommendations", "lesson", "ai-opportunity"],
            days=65,
            related=["M-030", "M-031"],
        )
    )

    # ── ADDITIONAL SUPPORTING MEMORIES ────────────────────────────────
    memories.append(
        m(
            "M-040",
            MemoryType.FEATURE,
            "Global Search is a high-frequency feature",
            "Search is among the top-3 most used product surfaces by session frequency.",
            feature_area="search",
            tags=["search", "usage"],
            metrics={"usage_rank": 2, "sessions_with_search": 0.74},
            days=22,
        )
    )
    memories.append(
        m(
            "M-041",
            MemoryType.OUTCOME,
            "Single-page checkout retained high completion after redesign of styling",
            "Visual refresh of checkout kept the single-page structure; completion stayed high.",
            outcome="After a purely visual redesign of checkout (same field count and flow), completion remained at 80%+.",
            feature_area="checkout",
            tags=["checkout", "outcome"],
            metrics={"completion_rate": 0.80},
            days=90,
            related=["M-012"],
        )
    )

    return memories


async def seed_if_empty(client) -> int:
    """Seed the memory store if it is empty. Returns number of memories seeded."""
    if client.count() > 0:
        return 0
    units = build_seed_memories()
    for u in units:
        await client.retain_unit(u)
    return len(units)