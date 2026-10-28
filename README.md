# 桌宠制作与联动工作流

这是一个 Codex 技能，用来制作或调整独立 macOS 桌宠：从用户提供的图片和音视频出发，完成音频切句、字幕、交互、桌宠间联动及验证。

技能总结了现有桌宠项目的做法，也包含一个可复用的 WAV 切分工具。默认音量、应用位置和联动协议来自现有项目；用于其他环境时应先检查并按实际需求调整。

## 使用

将 `skills/desktop-pet-workflow` 目录复制到 `~/.codex/skills/desktop-pet-workflow`，然后在 Codex 中调用 `$desktop-pet-workflow`。技能入口和细节分别见 `SKILL.md` 与 `references/`。

`scripts/cut_clips.py` 可根据 JSON 时间清单切分 16 位 PCM WAV，生成音频与清单。它使用 Python 标准库，并要求输出目录不存在，避免覆盖原文件或已有结果。

## 范围

本技能面向独立 macOS 桌宠，不是 ChatGPT Work 宠物技能。使用它不会自动发布素材或修改其他桌宠；具体工作以用户的要求和授权为准。

## 许可

技能文字和脚本按 [MIT](LICENSE) 许可发布。本仓库不包含桌宠人物图片、音频或视频。
