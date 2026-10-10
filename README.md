<div align="center">
  <img src="assets/readme-banner.svg" width="100%" alt="PaperArbor：让论文生长为知识，AI 驱动的中文论文精读与可视化知识库">
  <p>
    <a href="https://okinoyu.github.io/PaperArbor/">🌿 在线知识库</a> ·
    <a href="#-开始精读">🚀 开始精读</a> ·
    <a href="#-四种阅读方式">🧭 阅读方式</a> ·
    <a href="#-内容示例">📖 内容示例</a>
  </p>
</div>

PaperArbor 把论文变成可理解、可复查、可积累的中文研究知识。输入 PDF、arXiv 链接或论文名称，由 Codex 核实原文、拆解方法、整理实验，再生成带图解、公式与来源定位的独立网页。

**[进入在线知识库 →](https://okinoyu.github.io/PaperArbor/)** 按方向、标签与阅读方式查找文章，新内容同步到这里。

## ✨ 特点

| 🔬 深入机制 | 🌳 图文并读 |
| --- | --- |
| 从输入、数据流与训练信号讲清方法，保留消融、局限与未知项。 | 原论文图、流程图、离线公式与中文符号说明，串起关键步骤。 |
| **🔗 结论可追溯** | **📚 知识可积累** |
| 关键数字与结论附原文定位，证据索引区分事实、推导和分析。 | 搜索与分类聚合文章，支持手机阅读、打印和单文件离线阅读。 |

## 🚀 开始精读

在本项目根目录打开 Codex，调用仓库自带的 [`paper-arbor` Skill](.agents/skills/paper-arbor/SKILL.md)：

```text
$paper-arbor Single 精读这篇论文：/path/to/paper.pdf
$paper-arbor Series 梳理 Qwen-VL 系列的技术演进
$paper-arbor Digest 比较这些论文的潜在推理方法：……
$paper-arbor Radar 查找指定日期范围内的多模态推理论文
```

完成原文核查与站点校验后，将文章、证据和目录一起提交到 `main`，由 GitHub Pages 更新在线知识库。

## 🧭 四种阅读方式

| 模式 | 适合什么问题 |
| --- | --- |
| **Single · 单篇精读** | 一篇论文到底如何工作，证据支持什么？ |
| **Series · 系列演进** | 一条技术路线继承、替换和改进了什么？ |
| **Digest · 主题综述** | 不同方法的假设、评测与适用边界有何差别？ |
| **Radar · 研究雷达** | 指定方向与日期范围内，有哪些值得继续读的论文？ |

覆盖 LLM、VLM、Multimodal、Reasoning、Agent、RL 与 Others；Radar 按需执行。

## 📖 内容示例

- [OPLD：把多模态 CoT 蒸馏到潜在推理轨迹](https://okinoyu.github.io/PaperArbor/examples/VLM/opld-2607.28154.html)
- [Qwen-VL 系列：从视觉摘要到多模态推理](https://okinoyu.github.io/PaperArbor/examples/VLM/QwenVL-series.html)

## 🛠️ 本地维护

网站使用原生 HTML / CSS / JavaScript；维护脚本使用 Python 3.9+，无需数据库或后端。

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_index.py --check
python3 scripts/validate_site.py --json
python3 -m http.server 8000
```

本地预览：`http://localhost:8000`。文章位于 `examples/`，目录与证据位于 `data/`；新增内容遵循 [研究与发布规范](AGENTS.md) 和 [元数据格式](docs/metadata.md)。

Codex 负责研究与写作，脚本负责处理与校验；静态检查不能替代原文核实。本次无法获取或论文未公开的信息会明确标注。

## 📄 许可与致谢

原创内容采用 [MIT](LICENSE)；嵌入的论文图与其他第三方材料保留各自版权与来源。工作流参考 [PaperReading-skills](https://github.com/Linchunhui/PaperReading-skills)，README 排版参考 [MMSkills](https://github.com/DeepExperience/MMSkills)。
