"""Visual-planning node that chooses a future asset tool without executing it."""

from contentflow.config import Settings
from contentflow.llm_client import create_deepseek_client
from contentflow.models import VisualPlan
from contentflow.observability import record_llm_usage
from contentflow.prompting import load_prompt
from contentflow.structured import parse_structured_output


class VisualPlannerInputError(ValueError):
    """Raised when visual planning receives unusable content or limits."""


class VisualPlannerConfigurationError(RuntimeError):
    """Raised when the configured LLM cannot run visual planning."""


VISUAL_INSTRUCTIONS = load_prompt("visual")


def normalize_max_assets(max_assets: int) -> int:
    """Keep visual planning bounded for cost and reviewability."""
    if not 1 <= max_assets <= 5:
        raise VisualPlannerInputError("max_assets must be between 1 and 5.")
    return max_assets


def build_visual_messages(final_content: str, *, max_assets: int = 3) -> list[dict[str, str]]:
    """Build a bounded visual-planning request from reviewed content."""
    normalized_content = final_content.strip()
    if not normalized_content:
        raise VisualPlannerInputError("Final content must not be empty.")
    bounded_max_assets = normalize_max_assets(max_assets)
    return [
        {"role": "system", "content": VISUAL_INSTRUCTIONS},
        {
            "role": "user",
            "content": (
                f"最多规划 {bounded_max_assets} 个视觉素材。\n\n"
                f"请分析以下已经审核的最终内容：\n\n{normalized_content}"
            ),
        },
    ]


def validate_visual_plan(plan: VisualPlan, final_content: str, *, max_assets: int) -> VisualPlan:
    """Ensure the planned assets are grounded in the supplied content and budget."""
    if len(plan.assets) > normalize_max_assets(max_assets):
        raise RuntimeError("Visual Planner exceeded the requested asset limit.")
    missing_anchors = [
        asset.section_anchor for asset in plan.assets if asset.section_anchor not in final_content
    ]
    if missing_anchors:
        raise RuntimeError(
            "Visual Planner returned anchors that are absent from the final content."
        )
    return plan


def create_visual_plan(
    final_content: str, *, max_assets: int = 3, settings: Settings | None = None
) -> VisualPlan:
    """Request and validate a visual plan; this function does not execute asset tools."""
    active_settings = settings or Settings.from_env()
    client = create_deepseek_client(
        active_settings,
        consumer_name="Visual Planner",
        error_type=VisualPlannerConfigurationError,
    )
    response = client.chat.completions.create(
        model=active_settings.llm_model,
        messages=build_visual_messages(final_content, max_assets=max_assets),
        response_format={"type": "json_object"},
        max_tokens=1800,
    )
    record_llm_usage(response, node="visual_planner")
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Visual Planner returned an empty response.")
    plan = parse_structured_output(content, VisualPlan)
    return validate_visual_plan(plan, final_content, max_assets=max_assets)
