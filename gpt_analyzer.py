from __future__ import annotations

import base64
from pathlib import Path

from openai import OpenAI


PROMPT_PATH = Path(__file__).parent / "templates" / "all_in_one_prompt.txt"


def load_prompt_template() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError("找不到 templates/all_in_one_prompt.txt。") from exc


def analyze_clothing_image(
    image_bytes: bytes,
    api_key: str,
    model: str = "gpt-5.5",
) -> str:
    """Analyze one image with exactly one OpenAI Responses API request."""
    if not api_key:
        raise ValueError("OPENAI_API_KEY 不能为空。")

    prompt = load_prompt_template()
    image_base64 = base64.b64encode(image_bytes).decode("ascii")
    image_data_url = f"data:image/jpeg;base64,{image_base64}"

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": image_data_url,
                        "detail": "high",
                    },
                ],
            }
        ],
    )

    output_text = (response.output_text or "").strip()
    if not output_text:
        raise RuntimeError("OpenAI 返回了空内容，请稍后重试。")
    return output_text
