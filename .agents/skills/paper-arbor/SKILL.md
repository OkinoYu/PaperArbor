---
name: paper-arbor
description: 深度阅读论文 PDF、arXiv URL 或论文名称，生成有来源的中文独立 HTML，并维护 PaperArbor 知识库。用于单篇精读、系列演进、多篇主题综述或按需研究雷达报告。
---

# PaperArbor

把论文变成可理解、可复查、可积累的研究知识。此 Skill 在 PaperArbor 仓库内使用；从当前工作目录向上寻找同时包含 `AGENTS.md`、`data/papers.json` 和 `scripts/publish_entry.py` 的根目录，先读 AGENTS.md。用户可显式使用 `$paper-arbor`，也可通过论文精读、系列演进、主题综述、研究动态请求触发。

## 选择模式

尊重显式模式。1 篇论文 → **Single**；有继承关系的多篇论文 → **Series**；独立论文围绕一个问题 → **Digest**；给研究方向与日期范围、未给固定论文 → **Radar**。关系不明时说明采用 Digest；无法识别主题或时间范围才询问必要信息。Radar 只执行本次报告，不设置后台或定时任务。

先读 [研究与证据规范](references/research.md)，然后只读选定模式：[Single](references/single.md)、[Series](references/series.md)、[Digest](references/digest.md)、[Radar](references/radar.md)。排版前读 [输出规范](references/output.md)。元数据格式见仓库 `docs/metadata.md`。

## 输入和输出

输入是本地 PDF、arXiv ID/URL、论文名或论文清单；可加模式、主题、分类、日期区间、输出范围。论文名需要消歧与主来源核实；本地 PDF 先核实首页，不以文件名当正式标题。默认中文，保留技术专名。

输出：`examples/<Category>/<stem>.html`、`data/evidence/<stem>.json`、更新的 `data/papers.json` 与 `index.html`。正文包含来源、范围、版本与覆盖限制。缓存与图片临时产物放 `work/<stem>/` 或临时目录。除明确修订外，不覆盖已有文章。不要自动推送或发布。

## 执行闭环

1. 查现有清单与目标路径，避免同模式同来源集合重复。确定输入、模式、范围和分类。
2. 用浏览器或 `python3 scripts/fetch_sources.py SOURCE -o work/STEM/sources` 获取、核实主论文；来源不可用时记录失败并尝试作者项目/原始 PDF。缓存不是解读。标题歧义不选第一个搜索结果。
3. 阅读方法、训练、推理、实验、消融、局限，建立证据表。重要数字、公式、图表有原文定位；先写理解与证据再排版。缺少全文时输出标明覆盖不足的报告，不能声称完成精读。
4. 作者式重新组织中文技术正文 HTML。逐模块交代输入/输出、变换、设计理由、训练信号和推理行为。适配论文类型，未公开部分直接说明。按对应模式规范画内联 SVG，保留必要原始图。
5. 可选用 `scripts/extract_figure.py` 提取图；看裁切，标注来源。将本地图片嵌到 body，再渲染（或者先渲染后嵌入）：
   ```sh
   python3 scripts/render_article.py work/STEM/body.html --title 'TITLE' --subtitle 'SCOPE' --category VLM --type Series -o work/STEM/draft.html
   python3 scripts/embed_images.py work/STEM/draft.html -o work/STEM/standalone.html
   ```
6. 按 `docs/metadata.md` 写 `entry.json` 和 `evidence.json`。每条证据有文章 anchor、版本化 source、statement 和具体 locator；区分原文事实与解释性推导。
7. 运行可预览的候选检查，再发布本地：
   ```sh
   python3 scripts/publish_entry.py work/STEM/entry.json --html work/STEM/standalone.html --evidence work/STEM/evidence.json --dry-run
   python3 scripts/publish_entry.py work/STEM/entry.json --html work/STEM/standalone.html --evidence work/STEM/evidence.json
   python3 scripts/build_index.py --check
   python3 scripts/validate_site.py --json
   ```
   初次发布不用 `--replace`。已存在时先核对是重复还是用户要求修订；修订保留 id/path/evidence/added，再使用 `--replace`。
8. 修复校验错误；能用浏览器时检查桌面/移动、目录、图表、公式与离线阅读。静态校验不证明科学事实正确，做一遍逐项原文复核。
9. 报告新增/修改路径、来源覆盖、验证结果和未解决限制。若因材料缺失只完成部分报告，明确写出；不把不可获取变成虚构分析。
