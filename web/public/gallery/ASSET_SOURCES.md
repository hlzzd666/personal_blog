# 展馆资源说明

## 本地程序化/生成资源

| 文件 | 用途 | 来源 |
| --- | --- | --- |
| `generated/calm-ocean-color-tile.png` | 步道两侧与场景外部海面材质 | 本地生成资源 |
| `generated/light-travertine-color-tile.png` | 主步道与人物展台的洞石材质 | 本地生成资源 |
| `generated/sunrise-ocean-panorama-seamless.png` | 晴日海天背景与环境反射 | 本地生成资源 |
| `generated/frame-relief-champagne-brass-tile.png` | 相框外层、角件与铭牌的黄铜浮雕纹理 | Image2 API，模型 `gpt-image-2` |
| `generated/roof-sail-sea-glass-tile.png` | 预留的帆膜纹理；当前开放式场景未使用 | Image2 API，模型 `gpt-image-2` |
| `generated/compass-rose-inlay.png` | 入口步道罗盘嵌花 | Image2 API，模型 `gpt-image-2` |

Image2 生成提示词保存在 `output/image2-gallery/` 对应的 `*-prompt.txt` 文件中。API key 仅通过进程环境变量使用，未写入代码、资源或仓库。

当前场景是开放式海上步道与双侧展台，不加载玻璃墙、顶棚、玻璃地面或室内水池相关材质。`champagne-brass-color-tile.png`、`gallery-frame-champagne-brass-tile.png`、`glass-micro-detail-tile.png`、`sunrise-ocean-panorama.png` 与 `roof-sail-sea-glass-tile.png` 均为保留资源，当前运行时未引用。
