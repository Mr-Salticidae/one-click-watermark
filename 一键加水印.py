# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import json
import platform
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any

import fitz
from PIL import Image, ImageDraw, ImageFont


WATERMARK_COLOR = (235, 235, 235)
PDF_RENDER_SCALE = 2

TRIAL_FOLDER = "尝鲜版"
FULL_FOLDER = "完整版"
CONFIG_FILE = "水印设置.json"
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}


@dataclass
class WatermarkSettings:
    trial_text: str = "鲸海拾贝所有，V：linn011028，查看完整版"
    full_text: str = "版权归鲸海拾贝所有"
    font_path: str = ""
    font_size: int = 48
    row_count: int = 2
    rotate_degrees: int = 25
    opacity_percent: int = 35


def app_folder() -> Path:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        for parent in executable.parents:
            if parent.suffix.lower() == ".app":
                return parent.parent
        return executable.parent
    return Path(__file__).resolve().parent


def system_font_candidates() -> list[Path]:
    current_system = platform.system().lower()
    candidates: list[Path] = []

    if current_system == "windows":
        candidates.extend(
            [
                Path("C:/Windows/Fonts/simsun.ttc"),
                Path("C:/Windows/Fonts/msyh.ttc"),
                Path("C:/Windows/Fonts/simhei.ttf"),
                Path("C:/Windows/Fonts/arial.ttf"),
            ]
        )
    elif current_system == "darwin":
        candidates.extend(
            [
                Path("/System/Library/Fonts/PingFang.ttc"),
                Path("/System/Library/Fonts/STHeiti Light.ttc"),
                Path("/System/Library/Fonts/STHeiti Medium.ttc"),
                Path("/Library/Fonts/Arial Unicode.ttf"),
                Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
                Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            ]
        )
    else:
        candidates.extend(
            [
                Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
                Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            ]
        )

    return candidates


def default_font_path() -> str:
    candidates = [
        app_folder() / "字体.ttf",
        app_folder() / "字体.ttc",
        *system_font_candidates(),
    ]
    for item in candidates:
        if item.exists():
            return str(item)
    raise FileNotFoundError(
        "没有找到可用字体。请在“水印设置.json”的 font_path 中填写字体文件路径，"
        "或把字体文件放到本工具同一文件夹并命名为“字体.ttf”或“字体.ttc”。"
    )


def config_path(folder: Path) -> Path:
    return folder / CONFIG_FILE


def load_settings(folder: Path) -> WatermarkSettings:
    path = config_path(folder)
    if not path.exists():
        try:
            font_file = default_font_path()
        except FileNotFoundError:
            font_file = ""
        settings = WatermarkSettings(font_path=font_file)
        save_settings(path, settings)
        return settings

    with path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = json.load(file)

    defaults = asdict(WatermarkSettings())
    defaults.update({key: value for key, value in data.items() if key in defaults})
    settings = WatermarkSettings(**defaults)
    normalize_settings(settings)
    return settings


def save_settings(path: Path, settings: WatermarkSettings) -> None:
    path.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def normalize_settings(settings: WatermarkSettings) -> None:
    settings.font_path = str(settings.font_path).strip().strip("\"'")
    settings.font_size = min(max(int(settings.font_size), 12), 300)
    settings.row_count = min(max(int(settings.row_count), 1), 20)
    settings.rotate_degrees = min(max(int(settings.rotate_degrees), -90), 90)
    settings.opacity_percent = min(max(int(settings.opacity_percent), 1), 100)


def prompt_text(label: str, current: str) -> str:
    value = input(f"{label}（回车保持：{current}）：").strip()
    return value if value else current


def prompt_int(label: str, current: int, min_value: int, max_value: int) -> int:
    while True:
        value = input(f"{label}（{min_value}-{max_value}，回车保持：{current}）：").strip()
        if not value:
            return current
        try:
            number = int(value)
        except ValueError:
            print("请输入整数。")
            continue
        if min_value <= number <= max_value:
            return number
        print(f"请输入 {min_value} 到 {max_value} 之间的整数。")


def customize_settings(folder: Path, settings: WatermarkSettings) -> WatermarkSettings:
    print(f"当前设置文件：{config_path(folder)}")
    print("如需长期修改，也可以直接编辑这个 JSON 文件。")
    change = input("是否现在修改水印设置？输入 y 修改，直接回车使用当前设置：").strip().lower()
    if change not in {"y", "yes"}:
        return settings

    settings.trial_text = prompt_text("尝鲜版水印文字", settings.trial_text)
    settings.full_text = prompt_text("完整版水印文字", settings.full_text)
    settings.font_path = prompt_text("字体文件路径", settings.font_path)
    settings.font_size = prompt_int("水印字号", settings.font_size, 12, 300)
    settings.row_count = prompt_int("每张图片水印行数", settings.row_count, 1, 20)
    settings.rotate_degrees = prompt_int("水印旋转角度", settings.rotate_degrees, -90, 90)
    settings.opacity_percent = prompt_int("水印透明度百分比", settings.opacity_percent, 1, 100)
    normalize_settings(settings)
    save_settings(config_path(folder), settings)
    print("设置已保存。")
    return settings


def text_size(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    bbox = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def fitted_font(text: str, image_size: tuple[int, int], settings: WatermarkSettings) -> ImageFont.FreeTypeFont:
    width, _ = image_size
    configured_font = settings.font_path.strip().strip("\"'")
    if configured_font and Path(configured_font).exists():
        font_file = configured_font
    else:
        font_file = default_font_path()
    font_size = settings.font_size

    min_font_size = min(18, font_size)
    while font_size >= min_font_size:
        font = ImageFont.truetype(font_file, font_size)
        text_width, _ = text_size(font, text)
        # 留出边距，避免小尺寸图片或竖图时水印文字被裁切得太多。
        if text_width <= width * 0.92 or font_size == min_font_size:
            return font
        font_size -= 2

    return ImageFont.truetype(font_file, min_font_size)


def rotated_text_stamp(text: str, font: ImageFont.FreeTypeFont, settings: WatermarkSettings) -> Image.Image:
    alpha = round(255 * settings.opacity_percent / 100)
    width, height = text_size(font, text)
    padding = max(font.size, 18)
    stamp = Image.new("RGBA", (width + padding * 2, height + padding * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(stamp)
    draw.text((padding, padding), text, font=font, fill=(*WATERMARK_COLOR, alpha))
    return stamp.rotate(settings.rotate_degrees, expand=True, resample=Image.Resampling.BICUBIC)


def row_positions(height: int, stamp_height: int, row_count: int) -> list[int]:
    margin = max(8, stamp_height // 3)
    min_y = margin
    max_y = max(min_y, height - margin)
    if row_count == 1:
        return [height // 2]

    step = (max_y - min_y) / max(row_count - 1, 1)
    return [round(min_y + step * index) for index in range(row_count)]


def diagonal_step(stamp_width: int) -> tuple[int, int]:
    step = max(round(stamp_width * 1.25), 180)
    # PIL 的正角度旋转对应视觉上的左下到右上方向；摆放时也沿这个方向重复。
    dx = round(step * 0.91)
    dy = -round(step * 0.42)
    return dx, dy


def add_watermark_to_image(image: Image.Image, text: str, settings: WatermarkSettings) -> Image.Image:
    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    font = fitted_font(text, base.size, settings)
    stamp = rotated_text_stamp(text, font, settings)
    dx, dy = diagonal_step(stamp.width)
    repeat_count = max(6, round((base.width + base.height + stamp.width + stamp.height) / max(abs(dx), 1)) + 4)
    center_x = base.width // 2

    for row, center_y in enumerate(row_positions(base.height, stamp.height, settings.row_count)):
        row_offset = (row % 2) * 0.5
        for index in range(-repeat_count, repeat_count + 1):
            offset = index + row_offset
            x = round(center_x + offset * dx - stamp.width / 2)
            y = round(center_y + offset * dy - stamp.height / 2)
            overlay.alpha_composite(stamp, (x, y))

    return Image.alpha_composite(base, overlay)


def save_image(result: Image.Image, source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.lower()

    if suffix in {".jpg", ".jpeg"}:
        result.convert("RGB").save(target, quality=95, subsampling=0)
    else:
        result.save(target)


def process_image_file(source: Path, target: Path, text: str, settings: WatermarkSettings) -> None:
    with Image.open(source) as image:
        result = add_watermark_to_image(image, text, settings)
        save_image(result, source, target)


def process_pdf_file(source: Path, target: Path, text: str, settings: WatermarkSettings) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    matrix = fitz.Matrix(PDF_RENDER_SCALE, PDF_RENDER_SCALE)
    pages: list[Image.Image] = []

    with fitz.open(source) as document:
        for page in document:
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            pages.append(add_watermark_to_image(image, text, settings).convert("RGB"))

    if not pages:
        return

    first_page, other_pages = pages[0], pages[1:]
    first_page.save(target, "PDF", save_all=True, append_images=other_pages, resolution=144)


def process_file(source: Path, target: Path, text: str, settings: WatermarkSettings) -> None:
    if source.suffix.lower() == ".pdf":
        process_pdf_file(source, target, text, settings)
    else:
        process_image_file(source, target, text, settings)


def source_files(folder: Path) -> list[Path]:
    ignored = {TRIAL_FOLDER, FULL_FOLDER, "build", "dist", "__pycache__", "_水印测试"}
    files = []
    for item in folder.iterdir():
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS and item.parent.name not in ignored:
            files.append(item)
    return sorted(files, key=lambda p: p.name.lower())


def main() -> int:
    folder = app_folder()
    trial_dir = folder / TRIAL_FOLDER
    full_dir = folder / FULL_FOLDER
    files = source_files(folder)
    settings = customize_settings(folder, load_settings(folder))

    print("一键加水印工具")
    print(f"当前文件夹：{folder}")
    print(f"水印字号：{settings.font_size}，行数：{settings.row_count}，透明度：{settings.opacity_percent}%")
    print()

    if not files:
        print("没有找到 PNG、JPG、JPEG 或 PDF 文件。")
        print("请把要处理的文件放到本工具同一个文件夹里，然后重新双击运行。")
        input("\n按回车键退出...")
        return 1

    total = len(files)
    print(f"找到 {total} 个文件，开始生成水印文件...")

    for index, source in enumerate(files, start=1):
        print(f"[{index}/{total}] {source.name}")
        process_file(source, trial_dir / source.name, settings.trial_text, settings)
        process_file(source, full_dir / source.name, settings.full_text, settings)

    print()
    print("处理完成。")
    print(f"尝鲜版输出：{trial_dir}")
    print(f"完整版输出：{full_dir}")
    input("\n按回车键退出...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
