# 本地内容包示例

使用 Python 标准库检查输入清单和本地图片，生成待人工审核的内容包。不联网、不登录、不调用模型，不包含发布功能。

## 功能

- 校验标题、正文、标签、完整日期时间和页面角色。
- 检查显式人工审核字段及 PNG/JPEG/WebP 文件头。
- 计算 SHA-256，按清单顺序复制图片。
- 生成发布包和素材清单，始终记录 `submitted: false`。
- 拒绝覆盖已有输出目录。

文件头检查不包含完整图片解码或视觉识别。事实、图中文字、物体结构、日期和编号需要人工检查，审核字段应反映实际检查结果。

## 环境要求

Python 3.10 或更新版本，无第三方依赖。以下命令在仓库根目录执行；Windows 也可使用 `py -3` 代替 `python`。

## 校验默认输入

```powershell
python examples/prepare.py examples/sample.json
```

默认输入缺少图片，审核字段为 `false`，预期返回 `ok: false` 和退出码 `2`。

## 使用自定义输入

1. 复制 `examples/sample.json` 为 `examples/my-note.json`。
2. 在 `examples/assets` 放入图片，更新清单中的相对路径。
3. 填写编号、标题、正文、标签和完整计划时间。
4. `expected_roles` 与 `media` 中的角色和顺序保持一致。
5. 人工检查事实、图片与封面信息后，将相应审核字段设为 `true`。
6. 运行校验；需要组包时指定输出目录。

```powershell
python examples/prepare.py examples/my-note.json
python examples/prepare.py examples/my-note.json --out examples/practice-output
```

输出目录必须不存在。组包成功只表示本地资料准备完成，后续仍需人工审核与平台提交。

## 输出结构

```text
practice-output/
  发布包.txt
  images/
  manifest.json
```

`manifest.json` 记录编号、计划时间、图片角色、来源相对路径、输出路径、SHA-256 和未提交状态：

```text
production_status: PACKAGE_READY
review_status: PENDING_FINAL_HUMAN_REVIEW
platform_status: NOT_SUBMITTED
submitted: false
```

示例未集成飞书、文案生成、生图、Easel 或浏览器接口。完整工作流见[上手指南](../02-从零复现指南.md)。
