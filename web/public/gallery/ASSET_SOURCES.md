# 展馆资源来源

## 旗舰船舱

| 资源 | 用途 | 来源 |
| --- | --- | --- |
| `flagship/flagship.glb` | 船舱、前后甲板、相框 | 本地 Blender 4.2 建模；可复现脚本 `scripts/gallery/build_flagship.py` |
| `flagship/materials/teak-*` | 地板柚木 | Image2 API 基于主视角图提取颜色纹理，再派生粗糙度与法线 |
| `flagship/materials/walnut-*` | 拱肋、墙板胡桃木 | Image2 API 基于主视角图提取颜色纹理，再派生粗糙度与法线 |
| `flagship/materials/brass-*` | 黄铜相框与连接件 | 确定性程序纹理，PBR 金属度 0.86 |
| `flagship/materials/canvas-*` | 帆布顶 | 确定性程序织物纹理 |
| `generated/calm-ocean-color-tile.png` | 海面 | 既有本地生成资源 |

GLB 内嵌 12 张 PBR 图片。上述材质文件供重新建模使用，前台只请求 GLB 和海面纹理。天空使用 Three.js Sky，不使用远程图片。

主视角、俯视布局图、材质参考和生成记录保存在 `artifacts/gallery/reference/`；模型源文件、离线预览与验证报告保存在 `artifacts/gallery/model/`。接口模型为 `gpt-image-2`，元数据不包含密钥。完整提示词、实际输出尺寸和 SHA256 以相应生成目录为准。

## 资源清理

`generated/` 仅保留当前旗舰船舱实际加载的海面纹理；此前海上步道/玻璃展馆使用的石材、旧相框、罗盘、玻璃、帆膜和日出全景资源已移除，避免进入前台静态资源包。
