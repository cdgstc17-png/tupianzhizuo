from __future__ import annotations

import hashlib

import streamlit as st

from gpt_analyzer import analyze_clothing_image
from image_processor import process_uploaded_image
from text_splitter import split_all_prompts
from zip_utils import build_readme, create_material_zip


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

    st.subheader("GPT 输出预览")
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
st.caption("上传一张衣服图片，一次 GPT 分析后生成 ComfyUI / Wan2.2 前期素材。")

with st.expander("使用说明", expanded=True):
    st.markdown(
        """
1. 上传一张清晰的衣服图片，支持 JPG、JPEG、PNG、WEBP。
2. 点击“生成素材包”。程序会制作多种白底参考图，并调用一次 GPT 分析图片。
3. 生成完成后，可预览文字结果并下载 ZIP。

图片会等比例缩放并使用白色补边，不会拉伸，也不会裁掉衣服主体。  
本工具只准备素材，不会调用 ComfyUI，也不会自动生成视频。
"""
    )

uploaded_file = st.file_uploader(
    "上传衣服图片",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=False,
)

if uploaded_file is not None:
    uploaded_bytes = uploaded_file.getvalue()
    file_hash = hashlib.sha256(uploaded_bytes).hexdigest()

    st.image(uploaded_bytes, caption=f"已上传：{uploaded_file.name}")

    cache = get_result_cache()
    if file_hash in cache:
        st.info("这张图片在当前会话中已经生成过，已直接复用结果，不会再次调用 GPT。")
        render_result(cache[file_hash])

    if st.button("生成素材包", type="primary", use_container_width=True):
        if file_hash in cache:
            st.info("已复用现有结果，没有重复调用 GPT。")
        else:
            try:
                api_key = st.secrets["OPENAI_API_KEY"]
                model = st.secrets.get("OPENAI_MODEL", "gpt-5.5")
            except Exception:
                st.error(
                    "尚未配置 OPENAI_API_KEY。请在 Streamlit Cloud 的应用设置中添加 Secrets。"
                )
                st.stop()

            try:
                with st.status("正在生成素材包，请稍候……", expanded=True) as status:
                    st.write("1/4 正在制作不同尺寸的参考图片")
                    image_files = process_uploaded_image(uploaded_bytes)

                    st.write(f"2/4 正在使用 {model} 分析衣服图片（仅调用一次）")
                    gpt_output = analyze_clothing_image(
                        image_bytes=image_files["compressed_for_gpt.jpg"],
                        api_key=api_key,
                        model=model,
                    )

                    st.write("3/4 正在拆分提示词文件")
                    text_files = split_all_prompts(gpt_output)

                    st.write("4/4 正在打包 ZIP")
                    readme_text = build_readme(model=model)
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
                cache[file_hash] = result
                render_result(result)
            except Exception as exc:
                st.error(f"生成失败：{exc}")
                st.info(
                    "请检查 OpenAI API Key、模型名称、账户额度和网络连接，然后再试一次。"
                )
else:
    st.info("请先上传一张衣服图片。")

st.divider()
st.caption("隐私提示：上传图片会发送给 OpenAI API 进行一次多模态分析。")
