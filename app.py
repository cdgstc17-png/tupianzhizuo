from __future__ import annotations

import hashlib

import streamlit as st

from gpt_analyzer import analyze_clothing_image
from image_processor import process_uploaded_image
from text_splitter import split_all_prompts
from zip_utils import build_readme, create_material_zip


FREE_MODE = "免费手动模式（默认，不调用 API）"
API_MODE = "API 自动模式（调用一次 OpenAI）"


st.set_page_config(
    page_title="服装图片前期素材包",
    page_icon="👗",
    layout="centered",
)


def get_result_cache() -> dict:
    """Return the per-browser-session result cache."""
    if "result_cache" not in st.session_state:
        st.session_state.result_cache = {}
    return st.session_state.result_cache


def render_result(result: dict) -> None:
    st.success("素材包已生成，可以预览并下载。")

    st.subheader("完整文本预览")
    st.text_area(
        "all_prompts.txt",
        value=result["gpt_output"],
        height=420,
        disabled=True,
        label_visibility="collapsed",
    )

    st.download_button(
        label="下载 ZIP 素材包",
        data=result["zip_bytes"],
        file_name=result["zip_name"],
        mime="application/zip",
        use_container_width=True,
    )


st.title("👗 服装图片前期素材包")
st.info(
    "免费模式：先把图片发给 ChatGPT，再把 ChatGPT 输出粘贴到这里，"
    "本网页只负责整理和打包，不产生 API 费用。"
)

selected_mode = st.radio(
    "选择处理模式",
    options=[FREE_MODE, API_MODE],
    index=0,
    horizontal=True,
)

with st.expander("使用说明", expanded=True):
    if selected_mode == FREE_MODE:
        st.markdown(
            """
1. 先把衣服图片发送给 ChatGPT，并让它按照六个固定标题生成完整内容。
2. 回到本页上传同一张图片，再把 ChatGPT 输出粘贴到下方文本框。
3. 点击“生成素材包”，网页只处理图片、拆分文本并打包 ZIP，不调用 API。

图片会等比例缩放并使用白色补边，不会拉伸，也不会裁掉衣服主体。  
本工具只准备素材，不会调用 ComfyUI，也不会自动生成视频。
"""
        )
    else:
        st.markdown(
            """
1. 上传一张清晰的衣服图片，支持 JPG、JPEG、PNG、WEBP。
2. 点击“生成素材包”，网页会调用一次 OpenAI 多模态 API 自动分析。
3. 生成完成后，可预览文字结果并下载 ZIP。

API 自动模式需要在 Streamlit Secrets 中配置 OpenAI API Key，并会产生 API 费用。
"""
        )

manual_output = ""
if selected_mode == FREE_MODE:
    manual_output = st.text_area(
        "粘贴 ChatGPT 输出内容",
        height=420,
        placeholder=(
            "请粘贴包含【1. 服装分析】到"
            "【6. Wan2.2 人物动作提示词】六个固定标题的完整内容。"
        ),
    )
    with st.expander("查看必须保留的六个固定标题"):
        st.code(
            """【1. 服装分析】
【2. 对镜自拍视频脚本】
【3. 脚本画面分析】
【4. 人物九视图生成提示词】
【5. 服装九视图生成提示词】
【6. Wan2.2 人物动作提示词】""",
            language="text",
        )
else:
    st.warning("API 自动模式会把压缩后的图片发送给 OpenAI，并可能产生费用。")

uploaded_file = st.file_uploader(
    "上传衣服图片",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=False,
)

if uploaded_file is not None:
    uploaded_bytes = uploaded_file.getvalue()
    file_hash = hashlib.sha256(uploaded_bytes).hexdigest()
    st.image(uploaded_bytes, caption=f"已上传：{uploaded_file.name}")

    if selected_mode == FREE_MODE:
        text_hash = hashlib.sha256(manual_output.strip().encode("utf-8")).hexdigest()
        cache_key = f"free:{file_hash}:{text_hash}"
    else:
        cache_key = f"api:{file_hash}"

    if st.button("生成素材包", type="primary", use_container_width=True):
        cache = get_result_cache()
        if selected_mode == FREE_MODE and not manual_output.strip():
            st.error("请先在“粘贴 ChatGPT 输出内容”文本框中粘贴完整内容。")
        elif cache_key in cache:
            if selected_mode == API_MODE:
                st.info("已复用当前会话中的结果，没有重复调用 OpenAI API。")
            else:
                st.info("已复用相同图片和文本生成的素材包。")
        else:
            try:
                with st.status("正在生成素材包，请稍候……", expanded=True) as status:
                    total_steps = 4 if selected_mode == API_MODE else 3
                    st.write(f"1/{total_steps} 正在制作不同尺寸的参考图片")
                    image_files = process_uploaded_image(
                        uploaded_bytes,
                        include_gpt_image=selected_mode == API_MODE,
                    )

                    if selected_mode == API_MODE:
                        try:
                            api_key = st.secrets["OPENAI_API_KEY"]
                            model = st.secrets.get("OPENAI_MODEL", "gpt-5.5")
                        except Exception as exc:
                            raise RuntimeError(
                                "API 自动模式尚未配置 OPENAI_API_KEY。"
                                "请在 Streamlit Cloud 的 Secrets 中添加。"
                            ) from exc

                        st.write(f"2/4 正在使用 {model} 分析图片（仅调用一次）")
                        gpt_output = analyze_clothing_image(
                            image_bytes=image_files["compressed_for_gpt.jpg"],
                            api_key=api_key,
                            model=model,
                        )
                        readme_text = build_readme(mode="api", model=model)
                        split_step = "3/4"
                        zip_step = "4/4"
                    else:
                        gpt_output = manual_output.strip()
                        readme_text = build_readme(mode="free")
                        split_step = "2/3"
                        zip_step = "3/3"

                    st.write(f"{split_step} 正在拆分提示词文件")
                    text_files = split_all_prompts(gpt_output)

                    st.write(f"{zip_step} 正在打包 ZIP")
                    zip_bytes = create_material_zip(
                        image_files=image_files,
                        all_prompts=gpt_output,
                        split_text_files=text_files,
                        readme_text=readme_text,
                    )

                    status.update(label="素材包生成完成", state="complete", expanded=False)

                safe_stem = uploaded_file.name.rsplit(".", 1)[0]
                result = {
                    "gpt_output": gpt_output,
                    "zip_bytes": zip_bytes,
                    "zip_name": f"{safe_stem}_material_pack.zip",
                }
                cache[cache_key] = result
            except Exception as exc:
                st.error(f"生成失败：{exc}")
                if selected_mode == API_MODE:
                    st.info(
                        "请检查 OpenAI API Key、模型名称、账户额度和网络连接。"
                    )

    result_cache = get_result_cache()
    if cache_key in result_cache:
        render_result(result_cache[cache_key])
else:
    st.info("请先上传一张衣服图片。")

st.divider()
if selected_mode == FREE_MODE:
    st.caption("免费手动模式不会把图片或文字发送给 OpenAI API。")
else:
    st.caption("API 自动模式会把压缩后的图片发送给 OpenAI 进行一次多模态分析。")
