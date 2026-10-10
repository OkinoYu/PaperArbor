---
name: paper-arbor
description: 核实原始论文并深度拆解方法、训练和实验，生成循证中文离线 HTML。支持单篇精读、系列演进、主题综述、按需研究雷达，以及 PaperArbor 知识库维护。
---

# PaperArbor

把论文变成能复述机制、能核查结论、能长期复用的研究知识。默认中文，保留技术专名。脚本负责确定性处理，研究判断与正文由 agent 完成。

## 范围与交付

先读任务工作区 `AGENTS.md`，尊重本次范围与发布授权。寻找含 `scripts/render_article.py` 的 PaperArbor 根目录；当前目录不是项目时，可从本 Skill 实际路径向上查找。安装与路径约定见项目 `docs/usage.md`。从根目录运行脚本，输出到用户工作区或忽略目录。

- **Standalone**：只交付自包含 HTML 与 Evidence JSON，不修改 catalog；渲染加 `--standalone`。
- **Library**：维护文章、证据、catalog 与生成的 index，先做候选发布检查。本地发布不等于远程部署。
- 未指定交付方式：在 PaperArbor 项目内采用 Library，在其他工作区采用 Standalone。明确范围优先；安装 Skill 不代表授权发布。

尊重显式模式；一篇 → Single；有继承关系 → Series；独立论文围绕问题 → Digest；方向与日期范围、未给论文 → Radar。关系不明确时按 Digest 并说明。Radar 是一次发现报告。

## 按任务加载规范

1. 开始研究读 [research.md](references/research.md)：身份、版本、证据与范围。
2. 读模式：[Single](references/single.md) / [Series](references/series.md) / [Digest](references/digest.md) / [Radar](references/radar.md)。Single / Series 再读 [mechanisms.md](references/mechanisms.md)。
3. 排版读 [output.md](references/output.md) 与 [visuals.md](references/visuals.md)：组件、图形取舍、引用交互。
4. 交付前读 [quality.md](references/quality.md)：科学复核、阅读验收、确定性检查。

元数据格式以项目 `docs/metadata.md` 为准。不要为满足固定字数、图数或章节数而增补无证据内容。

## 工作闭环

**核实 → 证据与讲解提纲 → 正文与图形 → 渲染 → 双重验收 → 交付。**

- 查现有来源集合与目标路径。PDF 先核实首页；名称需消歧。用 `fetch_sources.py` 或原始官方来源获取材料，下载与裁切放 `work/<stem>/`。
- 阅读方法、训练、推理、实验与消融。先写主张—机制—证据关系，再写 HTML。别人的生成分析不是科学来源；已有笔记可帮助定位，承重结论仍核对原文。
- 为重要数值、公式、图表及设计主张写 Evidence claim，保留版本与 locator。缺全文时缩小范围并标明，不称完整精读。
- 按真实计算步骤写正文，使用稳定 ASCII anchor。渲染传 `--entry entry.json --evidence evidence.json`，把证据嵌入文件支持断网查证；`embed_images.py` 嵌入已检查的本地图像。
- Standalone 用 `validate_site.py --article standalone.html --entry entry.json --evidence evidence.json`；Library 先 `publish_entry.py … --dry-run` 再本地发布。修订用 `--replace`，保留 id/path/evidence/added；不覆盖文章试稿。
- 科学与桌面/手机检查通过后报告文件、覆盖限制与检查结果。远程推送依任务和项目授权；后续“保留本地”优先。
