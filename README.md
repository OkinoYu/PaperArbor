<div align="center">
  <img src="assets/logo.svg" width="72" alt="PaperArbor logo">
  <h1>PaperArbor</h1>
  <p><strong>An AI-Powered Visual Research Knowledge Base</strong></p>
  <p>Where Papers Grow into Knowledge.</p>
</div>

PaperArbor 是由 Codex 驱动的中文论文精读与可视化知识库。输入论文 PDF、arXiv URL 或论文名称，通过原生 `$paper-arbor` Skill 核实来源、拆解方法、生成独立 HTML，并同步维护网站索引。网页使用原生 HTML/CSS/JavaScript，维护工具使用 Python，不需要数据库、Node.js 或后端服务。

目标仓库：[`OkinoYu/PaperArbor`](https://github.com/OkinoYu/PaperArbor)。目标 Pages 地址：[`https://okinoyu.github.io/PaperArbor/`](https://okinoyu.github.io/PaperArbor/)。代码仓库与网站部署独立维护；GitHub Pages 尚未启用。

## 快速开始

Python 3.9+；网站阅读不需要 Python。下载或进入项目根目录：

```sh
python3 scripts/build_index.py
python3 scripts/validate_site.py
python3 -m http.server 8000
```

打开 [`http://localhost:8000`](http://localhost:8000)。也可直接打开 `index.html`：目录数据已嵌入页面，因此本地文件模式也支持搜索。文章单文件可复制到别处离线阅读，包含内联样式、脚本、SVG、MathML 和 base64 图像。普通来源链接与返回首页链接在离线/脱离网站时可能不可访问，但不影响正文阅读。

## 使用 Skill

在此项目根目录中打开 Codex，仓库 Skill 位于 `.agents/skills/paper-arbor/SKILL.md`。Codex 会自动发现这个目录；如果新增 Skill 未显示，重启 Codex 后再试，也可明确指定此文件。发现与调用机制见 [OpenAI 官方 Skill 文档](https://learn.chatgpt.com/docs/build-skills)。无需全局安装或额外模型 API Key。

```text
$paper-arbor Single 精读这篇论文：@paper.pdf
$paper-arbor Single 分析 https://arxiv.org/abs/2409.12191v2
$paper-arbor Series 梳理 Qwen-VL 到 Qwen3-VL 的演进
$paper-arbor Digest 比较这些独立论文如何处理长上下文：……
$paper-arbor Radar 发现 2026-10-03 至 2026-10-10 的多模态研究新论文
```

| 模式 | 输入 | 产出重点 |
|---|---|---|
| Single | 一篇已核实论文 | 动机、架构、方法、训练、推理、实验、消融和局限 |
| Series | 有技术继承关系的论文 | 时间线、跨代机制比较与逐代证据 |
| Digest | 围绕主题的独立论文 | 方法比较、假设边界与研究空白 |
| Radar | 研究方向与日期范围 | 按需发现、筛选、核实与来源状态；无后台服务 |

**Codex 负责研究分析与写作，脚本负责确定性处理。** 本项目不是一个无需审查即可自动生成科学结论的 LLM 服务。论文标题歧义、全文不可用和未公开细节需要如实处理；静态校验不能替代原文核查。

## 已有功能

- 七个方向：LLM、VLM、Multimodal、Reasoning、Agent、RL、Others。
- 首页全文元数据搜索、分类、标签、类型筛选，按收录/论文日期/标题排序，空结果提示与键盘快捷键 `/`。
- 静态卡片在关闭 JavaScript 时仍可进入文章；无需网络请求获取目录 JSON。
- 中文技术长文：桌面悬浮目录、移动折叠目录、锚点、阅读进度、打印、可横滚表格与图、可访问标签、减少动画支持。
- 离线 MathML 公式与中文说明，内联 SVG 流程和时间线，原论文图嵌入。
- 清单与证据 ledger；安全路径、重复检测、默认防覆盖、候选整站校验、发布锁与失败回滚。

## 首个真实示例

[`examples/VLM/QwenVL-series.html`](examples/VLM/QwenVL-series.html) 重新阅读四篇原始报告：Qwen-VL `2308.12966v1`、Qwen2-VL `2409.12191v2`、Qwen2.5-VL `2502.13923v1`、Qwen3-VL `2511.21631v2`。

包含十二个章节、跨代比较表、四张原创 SVG、五张原论文图、五条离线 MathML 说明式，以及 [`data/evidence/qwenvl-series.json`](data/evidence/qwenvl-series.json) 中的 51 条证据记录。保留训练计量差异、内部消融模型设置、指标退化项与长视频检索的适用范围；未复用参考网站的文章内容，也没有复跑完整训练与 benchmark。

## 新文章维护流程

从仓库根目录执行。工作文件放在被忽略的 `work/<stem>/`；正式发布位置由 metadata 决定。

1. 获取来源并核实正式标题、作者、日期、版本：
   ```sh
   python3 scripts/fetch_sources.py https://arxiv.org/abs/2409.12191v2 -o work/new-paper/sources
   ```
   支持 arXiv ID/URL、唯一标题匹配与本地 PDF。源文件不会覆盖已有缓存；本地 PDF 的标题/日期仍须读首页验证。arXiv ID 的 API 失败时尝试主站 abs 元数据并固定版本；论文标题搜索失败时使用浏览器或作者 PDF 补查，保留失败信息。
2. 由 Codex 写 `body.html`，使用唯一 `h2 id`，并在重要结论附近注明来源定位；同时写 `entry.json` 和 `evidence.json`。格式见 [`docs/metadata.md`](docs/metadata.md)。
3. 如需提取 PDF 图，安装**可选**依赖：
   ```sh
   python3 -m pip install -r requirements-figures.txt
   python3 scripts/extract_figure.py work/new-paper/sources/paper.pdf --page 4 --box 60 60 540 360 -o work/new-paper/figure.png
   ```
   页码从 1 开始，框坐标为 PDF points，次序是 `(x0, top, x1, bottom)`。必须视觉检查裁切、图注和小标签。PNG 默认最大宽 1600；常规图片目标 ≤350 KB，可为可读性保留并说明例外。
4. 渲染后嵌图：
   ```sh
   python3 scripts/render_article.py work/new-paper/body.html --title '论文精读' --subtitle '已核实论文与版本范围' --category LLM --type Single -o work/new-paper/draft.html
   python3 scripts/embed_images.py work/new-paper/draft.html -o work/new-paper/standalone.html
   ```
   `body.html` 的本地图片路径相对于草稿目录。嵌图工具不直接抓取远程图片；先下载、查看并核实。`srcset` 故意不支持，改用一张压缩后的图片。
5. 校验候选，再更新本地站点：
   ```sh
   python3 scripts/publish_entry.py work/new-paper/entry.json --html work/new-paper/standalone.html --evidence work/new-paper/evidence.json --dry-run
   python3 scripts/publish_entry.py work/new-paper/entry.json --html work/new-paper/standalone.html --evidence work/new-paper/evidence.json
   python3 scripts/build_index.py --check
   python3 scripts/validate_site.py --json
   ```
   发布器在临时副本验证全部页面，成功后更新 HTML、证据、清单、索引。已有记录默认拒绝；明确修订时使用 `--replace`，保持原有路径与 `added`。同一来源可同时有 Single 与 Series，但同类型同来源集合不能重复。

发布器是单进程的本地维护工具：每文件原子写入、异常回滚，**不是进程崩溃安全的多文件事务**。若维护进程被强制结束，检查站点与 `.publish.lock` 后再恢复，不要并发手改清单。

## 手动研究雷达

```sh
python3 scripts/radar.py --query 'cat:cs.CV AND all:multimodal' --start 2026-10-03 --end 2026-10-10 --limit 60 -o work/radar-candidates.json
```

输出候选 JSON，保留实际查询、UTC 日期语义、获取时间、来源成功/失败和是否可能截断；失败时保存状态并返回非零。Codex 随后做语义筛选、全文核查和报告写作。仅用摘要的发现必须标注为摘要级；报告不宣称穷尽全领域。初版只提供 arXiv one-shot 抓取，其他公开来源可在 Skill 中通过浏览器补充并明确披露覆盖。

## 测试与质量边界

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_index.py --check
python3 scripts/validate_site.py --json
```

验证清单同步、重复、站内文件/锚点、路径、图像嵌入、外部运行时、SVG/MathML XML 和证据 anchor。测试使用离线 Atom/PDF fixture，避免依赖网络稳定性；发布过程包含失败/回滚测试。外部链接不会由站点 validator 自动请求，原始事实仍须逐项复核。

初版验收结果见 [`docs/verification.md`](docs/verification.md)。未来适合增加更多真实 Single/Digest/Radar 示例、HF 等来源适配器、更细的 claim/split schema 与可选全文提取。当前四种模式工作流齐全，完整端到端真实内容验证集中在 Series 示例；没有后台、用户账户或模型推理服务。

## GitHub Pages 部署

本地已支持项目子路径，尚未执行下面的远程操作。部署方式参照 [GitHub 官方发布源文档](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)。准备好后将目录作为 `OkinoYu/PaperArbor` 仓库的 `main` 分支内容：

1. 在 GitHub 仓库 **Settings → Pages → Build and deployment** 选择 **Deploy from a branch**。
2. Branch 选择 **main**，Folder 选择 **/ (root)**，保存。
3. Pages 发布后访问 [`https://okinoyu.github.io/PaperArbor/`](https://okinoyu.github.io/PaperArbor/)。

`.nojekyll` 保留静态资源；站内链接都使用相对路径，文章返回首页为 `../../index.html`，因此 `/PaperArbor/` 不需要硬编码。GitHub Pages 只托管生成的文件，不执行 Python；修改清单后必须在本地运行构建/验证并一起提交生成索引。没有 Node 构建步骤或 server-side API。

## 项目结构

```text
.agents/skills/paper-arbor/   原生 Skill 与按模式加载的研究规范
AGENTS.md                   长期开发与研究质量约定
assets/                     独立品牌、首页资源及文章内联资源源文件
data/papers.json            统一目录清单
data/evidence/              逐项来源与证据
examples/<Category>/        自包含文章（按实际内容创建分类目录）
templates/index.html        索引源模板
scripts/                    获取、Radar、图提取、渲染、嵌入、发布、构建与校验
tests/                      标准库 unittest
docs/                      元数据、参考研究与验收记录
```

## 来源与许可证

工作流思想和论文长文形式参考 [`Linchunhui/PaperReading-skills`](https://github.com/Linchunhui/PaperReading-skills) 及其 [QwenVL 示例](https://linchunhui.github.io/PaperReading-skills/examples/VLM/QwenVL-series.html)。研究记录与独立设计说明见 [`docs/reference-study.md`](docs/reference-study.md)。PaperArbor 的代码、CSS、模板、Logo 与解读正文均独立编写，未复制上游 MIT 代码或生成文章；未来若复用其代码，需保留原版权与许可证。

原创项目内容使用 [MIT](LICENSE)。嵌入的原论文图保留作者版权及明确出处，不被项目 MIT 许可证重新授权；来源元数据标注 arXiv non-exclusive distribution license，未获得另行图形再许可。第三方内容的版权说明同时保留在文章和证据清单。
