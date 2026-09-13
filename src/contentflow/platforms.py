"""Platform-native planning and writing standards for ContentFlow."""

from dataclasses import dataclass

from contentflow.models import ContentPlatform


@dataclass(frozen=True)
class PlatformStandard:
    """The smallest structural contract for one publishable content format."""

    min_sections: int
    max_sections: int
    planner_steps: tuple[str, ...]
    writer_rules: tuple[str, ...]


PLATFORM_STANDARDS: dict[ContentPlatform, PlatformStandard] = {
    "长文章": PlatformStandard(
        5,
        7,
        ("标题与问题引入", "核心观点", "分段展开", "可执行建议", "总结"),
        ("使用一级标题和必要的二级标题。", "以连贯段落展开，不要写成列表堆砌。"),
    ),
    "公众号文章": PlatformStandard(
        5,
        7,
        ("标题与导语", "读者处境或问题", "核心观点", "案例或方法", "总结与行动建议"),
        ("保留标题、导语和清晰的小标题。", "结尾收束观点并给出行动建议。"),
    ),
    "小红书笔记": PlatformStandard(
        4,
        6,
        ("封面标题与痛点钩子", "核心方法或清单", "分点步骤", "避坑或提醒", "互动收尾与标签"),
        ("开头先给出可作封面的短标题和痛点钩子。", "用短句、分点和留白组织内容；不要改写成传统长文章。", "结尾给出互动引导和 3–8 个相关标签。"),
    ),
    "社交媒体文案": PlatformStandard(
        3,
        5,
        ("一句观点钩子", "核心论据或步骤", "补充提醒", "互动提问或行动引导"),
        ("首句必须独立、有明确观点或利益点。", "保持短段落，正文只保留最必要的信息。", "最后用一个具体问题或行动引导收尾。"),
    ),
    "PPT 大纲": PlatformStandard(
        5,
        10,
        ("封面页", "背景或问题", "核心观点", "分页面要点", "总结与下一步"),
        ("按“第 N 页：页面标题”的形式输出。", "每页最多 3–5 条短要点，避免完整论述段落。", "每页只表达一个中心意思。"),
    ),
    "短视频脚本": PlatformStandard(
        4,
        6,
        ("前 3 秒钩子", "问题或冲突", "口播要点", "例子或行动步骤", "结尾行动引导"),
        ("按镜头或口播节奏分段，不写成文章小标题。", "第一句必须适合前 3 秒口播。", "每一段保持口语化，并以行动引导结束。"),
    ),
}


def get_platform_standard(platform: ContentPlatform) -> PlatformStandard:
    """Return the validated structural standard for one supported platform."""
    return PLATFORM_STANDARDS[platform]


def build_platform_guidance(platform: ContentPlatform) -> str:
    """Build reusable, explicit instructions for both Planner and Writer."""
    standard = get_platform_standard(platform)
    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(standard.planner_steps, start=1))
    rules = "\n".join(f"- {rule}" for rule in standard.writer_rules)
    return (
        f"平台原生结构：{platform}\n"
        f"计划必须包含 {standard.min_sections} 至 {standard.max_sections} 个结构单元，按以下顺序组织：\n"
        f"{steps}\n\n"
        f"成稿规则：\n{rules}"
    )
