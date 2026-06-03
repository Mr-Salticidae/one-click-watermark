# One Click Watermark

一个简单的一键加水印工具，支持批量处理 PNG、JPG、JPEG 和 PDF 文件。

工具会在当前文件夹中查找待处理文件，并自动输出到两个文件夹：

- `尝鲜版`
- `完整版`

原始文件不会被修改。

## 功能

- 批量给图片和 PDF 添加水印
- 支持自定义水印文字、字体、字号、透明度、旋转角度
- 支持自定义每张图片的水印行数
- 支持 Windows 和 macOS
- 支持通过 PyInstaller 打包

## Windows 使用

1. 把 `一键加水印.exe` 和要处理的文件放在同一个文件夹。
2. 双击运行 `一键加水印.exe`。
3. 第一次运行会生成 `水印设置.json`。
4. 按提示选择是否修改水印设置。
5. 处理完成后查看 `尝鲜版` 和 `完整版` 文件夹。

## macOS 使用

先安装依赖：

```bash
python3 -m pip install pillow pymupdf
```

运行工具：

```bash
python3 一键加水印.py
```

## 水印设置

可以直接编辑 `水印设置.json`：

```json
{
  "trial_text": "鲸海拾贝所有，V：linn011028，查看完整版",
  "full_text": "版权归鲸海拾贝所有",
  "font_path": "C:\\Windows\\Fonts\\simsun.ttc",
  "font_size": 48,
  "row_count": 2,
  "rotate_degrees": 25,
  "opacity_percent": 35
}
```

字段说明：

- `trial_text`：尝鲜版水印文字
- `full_text`：完整版水印文字
- `font_path`：字体文件路径，留空时会自动查找系统常见字体
- `font_size`：水印字号，范围 12-300
- `row_count`：每张图片水印行数，范围 1-20
- `rotate_degrees`：水印旋转角度，范围 -90 到 90
- `opacity_percent`：水印透明度百分比，范围 1-100

如果字体识别失败，可以把字体文件放到工具同一文件夹，并命名为 `字体.ttf` 或 `字体.ttc`。

## 打包

安装 PyInstaller：

```bash
python -m pip install pyinstaller
```

打包：

```bash
pyinstaller 一键加水印.spec
```

Windows 会生成 `dist/一键加水印.exe`。macOS 需要在 macOS 系统上打包。

## 注意

- `build/`、`dist/` 和 `*.exe` 不提交到 Git 仓库。
- Windows 可执行文件体积较大，建议通过 GitHub Releases 发布。
