from __future__ import annotations

import re


SECTION_FILES = {
    "【1. 服装分析】": "clothing_analysis.txt",
    "【2. 对镜自拍视频脚本】": "script.txt",
    "【3. 脚本画面分析】": "scene_analysis.txt",
    "【4. 人物九视图生成提示词】": "character_9view_prompt.txt",
    "【5. 服装九视图生成提示词】": "garment_9view_prompt.txt",
    "【6. Wan2.2 人物动作提示词】": "motion_prompts.txt",
}


def split_all_prompts(text: str) -> dict[str, str]:
    """Split GPT output using the six fixed Chinese headings."""
    title_pattern = "|".join(re.escape(title) for title in SECTION_FILES)
    pattern = re.compile(
        rf"(?m)^\s*(?:\*\*)?({title_pattern})(?:\*\*)?\s*$"
    )
    matches = list(pattern.finditer(text))
    sections: dict[str, str] = {}

    for index, match in enumerate(matches):
        title = match.group(1)
        content_start = match.end()
        content_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[title] = text[content_start:content_end].strip()

    result: dict[str, str] = {}
    for title, filename in SECTION_FILES.items():
        content = sections.get(title, "").strip()
        if not content:
            content = (
                f"模型未按固定标题返回 {title} 分区。"
                "请查看 all_prompts.txt 获取完整原始输出。"
            )
        result[filename] = content + "\n"

    return result
