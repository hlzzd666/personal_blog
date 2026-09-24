"""把接口返回的原始画面导出为页面可直接叠放的 WebP 图层。"""

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT.parents[3] / "web" / "public" / "about"


def export_layer(source_name: str, output_name: str, alpha: bool) -> None:
    source = ROOT / source_name
    image = Image.open(source).convert("RGBA" if alpha else "RGB")
    if alpha:
        # 接口的透明层含 1–3/255 的无意义背景残留；只归零不可见噪声，保留索具抗锯齿。
        channel = image.getchannel("A")
        image.putalpha(channel.point(lambda value: 0 if value <= 3 else 255 if value >= 248 else round((value - 3) * 255 / 245)))
    target = PUBLIC / output_name
    image.save(target, "WEBP", quality=90 if alpha else 88, method=6, exact=alpha)
    provenance = {
        "source": str(source.relative_to(ROOT.parents[3])).replace("\\", "/"),
        "model": "gpt-image-2",
        "requested_quality": "high",
        "reported_quality": "medium" if alpha else "low",
        "prompt": (source.parent / "prompt.txt").read_text(encoding="utf-8"),
        "processing": "保留接口实际返回的 RGBA 蒙版，清除 alpha<=3 的透明噪声并将 alpha>=248 设为不透明；未使用几何裁切蒙版。" if alpha else "保持原始构图，仅导出压缩 WebP。",
        "size": list(image.size),
        "alpha": alpha,
    }
    target.with_suffix(target.suffix + ".json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{target.name}: {image.size}, {target.stat().st_size} bytes, alpha={alpha}, bounds={image.getbbox()}")
    if alpha:
        preview = Image.new("RGBA", image.size, "#0d2933")
        preview.alpha_composite(image)
        preview.convert("RGB").save(ROOT / "foreground" / "teal-preview-final.jpg", quality=95)


if __name__ == "__main__":
    export_layer("background/night-sea.png", "night-sea.webp", False)
    export_layer("foreground/night-workbench.png", "night-workbench.webp", True)
