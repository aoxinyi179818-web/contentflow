"""A deterministic local search tool used to learn Tool Calling safely."""

from pydantic import BaseModel, ConfigDict, Field


class ResearchSource(BaseModel):
    """One result from the local demonstration corpus."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: str
    url: str
    summary: str
    source_type: str = "demo_seed"


class SearchArguments(BaseModel):
    """Validated public input for the local search function."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=120)
    max_results: int = Field(default=3, ge=1, le=5)


DEMO_CORPUS = (
    ResearchSource(
        source_id="study-planning",
        title="学习计划的拆分方法",
        url="https://example.invalid/research/study-planning",
        summary="演示资料：将复习任务按课程、时间块和可检查产出拆分，并在每个时间块结束时记录完成情况。",
    ),
    ResearchSource(
        source_id="retrieval-practice",
        title="主动回忆的练习设计",
        url="https://example.invalid/research/retrieval-practice",
        summary="演示资料：用不看笔记的自测问题检查理解，再根据遗漏内容安排下一轮复习。",
    ),
    ResearchSource(
        source_id="source-literacy",
        title="资料可信度检查清单",
        url="https://example.invalid/research/source-literacy",
        summary="演示资料：记录作者或机构、发布日期、原始出处和结论适用范围，区分观点与可验证事实。",
    ),
    ResearchSource(
        source_id="privacy-boundary",
        title="学习工具中的隐私边界",
        url="https://example.invalid/research/privacy-boundary",
        summary="演示资料：在上传课程材料前先确认文件是否包含个人信息、课程限制或不可分享内容。",
    ),
)


def search_research_knowledge(arguments: SearchArguments) -> list[ResearchSource]:
    """Return relevant demonstration sources without accessing the web."""
    query_characters = {
        character for character in arguments.query.lower() if not character.isspace()
    }

    def relevance(source: ResearchSource) -> int:
        searchable = f"{source.title}{source.summary}".lower()
        return sum(character in searchable for character in query_characters)

    ranked_sources = sorted(DEMO_CORPUS, key=relevance, reverse=True)
    return [source for source in ranked_sources if relevance(source) > 0][: arguments.max_results]
