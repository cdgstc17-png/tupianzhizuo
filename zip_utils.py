from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile


def build_readme(mode: str, model: str | None = None) -> str:
    if mode == "api":
        source_description = f"文字内容由 OpenAI API 自动分析生成，模型：{model}"
        extra_image = """
5. compressed_for_gpt.jpg
   长边不超过 1024 像素的压缩图。本次 API 分析实际使用的图片。
"""
    else:
        source_description = "文字内容由用户从 ChatGPT 手动复制粘贴，本网页未调用 OpenAI API"
        extra_image = ""

    return f"""服装图片前期素材包使用说明
============================

{source_description}
本工具没有调用 ComfyUI，也没有生成视频。

图片文件
--------
1. original.png
   上传原图的 PNG 备份。

2. cloth_1x1.png
   1024x1024 白底方形参考图。适合服装参考、构图参考或方形预览。

3. cloth_9x16.png
   1080x1920 白底竖版参考图。适合竖屏画面、短视频构图和 Wan2.2 前期参考。

4. cloth_comfy_input.png
   832x1216 白底参考图。可作为 ComfyUI 工作流中的图像输入。

{extra_image}

文字文件
--------
1. all_prompts.txt
   ChatGPT 输出的完整原始内容。

2. clothing_analysis.txt
   服装品类、版型、颜色、面料、细节和视觉风格分析。

3. script.txt
   可用于时尚展示短片的镜头脚本草案。

4. scene_analysis.txt
   场景、灯光、色彩和镜头氛围建议。

5. character_9view_prompt.txt
   角色九视图提示词，可用于先建立统一人物参考。

6. garment_9view_prompt.txt
   服装九视图提示词，可用于建立统一服装参考。

7. motion_prompts.txt
   分镜运动提示词，可作为 Wan2.2 或其他视频工作流的前期文本素材。

建议流程
--------
1. 先阅读 clothing_analysis.txt，检查 GPT 是否正确理解衣服。
2. 使用 garment_9view_prompt.txt 和参考图建立服装一致性素材。
3. 如需固定人物，再使用 character_9view_prompt.txt 建立角色参考。
4. 根据 script.txt 和 scene_analysis.txt 准备场景与分镜。
5. 将 motion_prompts.txt 中的提示词逐条复制到自己的 ComfyUI / Wan2.2 工作流。

注意事项
--------
- AI 可能对图片中不可见的背面、面料或结构进行合理推测，请人工检查。
- 图片均采用等比例缩放和白色补边，没有拉伸或裁掉衣服主体。
- 请确保你对上传图片拥有合法使用权。
"""


def create_material_zip(
    image_files: dict[str, bytes],
    all_prompts: str,
    split_text_files: dict[str, str],
    readme_text: str,
) -> bytes:
    """Build the downloadable zip fully in memory."""
    output = BytesIO()
    with ZipFile(output, mode="w", compression=ZIP_DEFLATED) as archive:
        for filename, content in image_files.items():
            archive.writestr(filename, content)

        archive.writestr("all_prompts.txt", all_prompts.encode("utf-8"))
        for filename, content in split_text_files.items():
            archive.writestr(filename, content.encode("utf-8"))
        archive.writestr("README.txt", readme_text.encode("utf-8"))

    return output.getvalue()
