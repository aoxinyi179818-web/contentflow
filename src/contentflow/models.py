"""Validated data contracts for ContentFlow structured LLM output."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ContentPlatform = Literal[
    "长文章",
    "公众号文章",
    "小红书笔记",
    "社交媒体文案",
    "PPT 大纲",
    "短视频脚本",
]
ContentTone = Literal["清晰专业", "友好易懂", "启发思考", "简洁有力"]
ContentLength = Literal["短（约 300 字）", "中（约 800 字）", "长（约 1500 字）"]
FeedbackRating = Literal["有帮助", "需要改进"]
VisualAssetType = Literal["image", "chart"]
VisualTool = Literal["image_search", "image_generation", "chart"]

CONTENT_PLATFORM_OPTIONS: tuple[ContentPlatform, ...] = (
    "长文章",
    "公众号文章",
    "小红书笔记",
    "社交媒体文案",
    "PPT 大纲",
    "短视频脚本",
)
CONTENT_TONE_OPTIONS: tuple[ContentTone, ...] = ("清晰专业", "友好易懂", "启发思考", "简洁有力")
CONTENT_LENGTH_OPTIONS: tuple[ContentLength, ...] = (
    "短（约 300 字）",
    "中（约 800 字）",
    "长（约 1500 字）",
)
FEEDBACK_RATING_OPTIONS: tuple[FeedbackRating, ...] = ("有帮助", "需要改进")


class ContentPreferences(BaseModel):
    """User-controlled constraints that must survive the content workflow."""

    model_config = ConfigDict(extra="forbid")

    audience: str = Field(min_length=1, max_length=80)
    tone: ContentTone
    platform: ContentPlatform
    target_length: ContentLength


class ProjectFeedbackInput(BaseModel):
    """One user's latest quality judgment for a saved local project."""

    model_config = ConfigDict(extra="forbid")

    rating: FeedbackRating
    comment: str = Field(default="", max_length=500)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str) -> str:
        return value.strip()


class ContentSection(BaseModel):
    """One ordered section in a content plan."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)


class ContentPlan(BaseModel):
    """Planner output consumed by Writer."""

    model_config = ConfigDict(extra="forbid")

    topic: str = Field(min_length=1)
    audience: str = Field(min_length=1)
    tone: str = Field(min_length=1)
    platform: ContentPlatform = "长文章"
    target_length: ContentLength = "中（约 800 字）"
    sections: list[ContentSection] = Field(min_length=5, max_length=7)
    scope_note: str | None = None


class ReviewProblem(BaseModel):
    """One actionable issue found in a draft."""

    model_config = ConfigDict(extra="forbid")

    problem_type: str = Field(min_length=1)
    severity: Literal["高", "中", "低"]
    location: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    suggestion: str = Field(min_length=1)


class ReviewReport(BaseModel):
    """Reviewer output consumed by Rewrite and future quality routing."""

    evidence_score: int = Field(default=25, ge=0, le=25)
    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1)
    structure_score: int = Field(ge=0, le=25)
    clarity_score: int = Field(ge=0, le=25)
    audience_tone_score: int = Field(ge=0, le=25)
    completeness_score: int = Field(ge=0, le=25)
    problems: list[ReviewProblem] = Field(default_factory=list)
    priority_suggestions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_dimension_total(self) -> "ReviewReport":
        dimension_total = (
            self.structure_score
            + self.clarity_score
            + self.audience_tone_score
            + self.completeness_score
        )
        if self.score != dimension_total:
            raise ValueError("score must equal the sum of the four dimension scores")
        return self


class AdaptedContent(BaseModel):
    """Validated final content tailored to one supported output platform."""

    model_config = ConfigDict(extra="forbid")

    platform: ContentPlatform
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    format_notes: list[str] = Field(default_factory=list)


class VisualAssetPlan(BaseModel):
    """One grounded recommendation for a future visual asset tool call."""

    model_config = ConfigDict(extra="forbid")

    section_anchor: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    asset_type: VisualAssetType
    tool: VisualTool
    query_or_prompt: str = Field(min_length=1)
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_matching_tool_and_asset_type(self) -> "VisualAssetPlan":
        expected_type = "chart" if self.tool == "chart" else "image"
        if self.asset_type != expected_type:
            raise ValueError("asset_type must match the selected visual tool")
        return self


class VisualPlan(BaseModel):
    """Validated, bounded visual recommendations for completed content."""

    model_config = ConfigDict(extra="forbid")

    overview: str = Field(min_length=1)
    assets: list[VisualAssetPlan] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_unique_anchors(self) -> "VisualPlan":
        anchors = [asset.section_anchor for asset in self.assets]
        if len(anchors) != len(set(anchors)):
            raise ValueError("visual assets must use unique section anchors")
        return self
