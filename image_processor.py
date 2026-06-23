from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError


SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}


def _open_image(image_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(image_bytes))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("无法读取图片，请上传有效的 JPG、PNG 或 WEBP 文件。") from exc

    if image.format not in SUPPORTED_FORMATS:
        raise ValueError("不支持该图片格式，请上传 JPG、JPEG、PNG 或 WEBP。")

    return ImageOps.exif_transpose(image)


def _flatten_to_rgb(image: Image.Image, background: str = "white") -> Image.Image:
    """Convert any Pillow image mode to RGB, flattening transparency on white."""
    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        rgba = image.convert("RGBA")
        canvas = Image.new("RGBA", rgba.size, background)
        canvas.alpha_composite(rgba)
        return canvas.convert("RGB")
    return image.convert("RGB")


def _save_png(image: Image.Image) -> bytes:
    if image.mode not in ("1", "L", "LA", "P", "RGB", "RGBA", "I", "I;16"):
        image = image.convert("RGB")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _make_white_canvas(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Fit the full image inside an exact white canvas without cropping."""
    source = _flatten_to_rgb(image)
    fitted = ImageOps.contain(source, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    left = (size[0] - fitted.width) // 2
    top = (size[1] - fitted.height) // 2
    canvas.paste(fitted, (left, top))
    return canvas


def _make_gpt_jpeg(image: Image.Image, max_edge: int = 1024) -> bytes:
    source = _flatten_to_rgb(image)
    source.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
    output = BytesIO()
    source.save(
        output,
        format="JPEG",
        quality=85,
        optimize=True,
        progressive=True,
    )
    return output.getvalue()


def process_uploaded_image(image_bytes: bytes) -> dict[str, bytes]:
    """
    Create all required image assets.

    Every resized reference keeps the original aspect ratio and uses white
    padding, so the garment is neither stretched nor cropped.
    """
    image = _open_image(image_bytes)

    return {
        "original.png": _save_png(image),
        "cloth_1x1.png": _save_png(_make_white_canvas(image, (1024, 1024))),
        "cloth_9x16.png": _save_png(_make_white_canvas(image, (1080, 1920))),
        "cloth_comfy_input.png": _save_png(
            _make_white_canvas(image, (832, 1216))
        ),
        "compressed_for_gpt.jpg": _make_gpt_jpeg(image),
    }
