<div align="center">
  <img src="assets/readme-banner.svg" width="100%" alt="PaperArbor：让论文生长为知识，AI 驱动的中文论文精读与可视化知识库">
  <p><a href="https://okinoyu.github.io/PaperArbor/">🌿 在线知识库</a> · <a href="#-开始精读">🚀 开始精读</a> · <a href="docs/usage.md">安装与使用</a></p>
</div>

PaperArbor 把论文变成可理解、可复查、可积累的中文研究知识。用 Codex 核实原文、拆解方法与实验，生成带图解、公式和来源证据的独立网页。

## ✨ 特点

- **读懂机制**：沿样本解释输入、变换、输出、监督及设计原因，分开训练与推理。
- **图文并读**：原论文图、解释性 SVG、离线 MathML；桌面/手机导航与跨代对比。
- **就地查证**：版本与 SHA-256、Evidence JSON、离线搜索证据和返回正文；事实、推导、分析分开。
- **两种交付**：独立 HTML + 证据清单，或维护可搜索的静态知识库。无需模型 API、数据库或后端。

## 🚀 开始精读

```sh
git clone https://github.com/OkinoYu/PaperArbor.git
cd PaperArbor
```

在目录内打开 Codex，调用 [`paper-arbor`](.agents/skills/paper-arbor/SKILL.md)：

```text
$paper-arbor Single 精读 /path/paper.pdf，Standalone，交付离线 HTML 与证据清单
$paper-arbor Series 梳理 Qwen-VL → Qwen3.5，Library，先保留本地
$paper-arbor Digest 比较这些论文的方法、假设与评测：……
$paper-arbor Radar 查找指定方向与日期范围的论文
```

Python 3.9+ 负责维护；PDF 提图依赖按需安装。其他项目安装、完整命令与发布范围见 **[使用指南](docs/usage.md)**。脚本不自动做科学推理，也不自动推送。

## 📖 示例

- [Qwen-VL → Qwen3.5：机制演进](https://okinoyu.github.io/PaperArbor/examples/VLM/QwenVL-series.html)
- [OPLD：多模态潜在推理蒸馏](https://okinoyu.github.io/PaperArbor/examples/VLM/opld-2607.28154.html)

网站按方向、标签与阅读方式查找；示例的本地修改只有明确发布后才会上线。

## 🛠️ 验证与维护

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_index.py --check
python3 scripts/validate_site.py --json
python3 -m http.server 8000
```

[元数据与证据格式](docs/metadata.md) · [项目约定](AGENTS.md) · [参考对比](docs/reference-study.md)。静态检查不能替代原文复核；未知或未公开的信息明确标记。

## 📄 许可与致谢

原创代码与解读采用 [MIT](LICENSE)，论文图与其他第三方材料保留原版权。工作流设计参考 [PaperReading-skills](https://github.com/Linchunhui/PaperReading-skills)，本项目独立实现证据、知识库与阅读组件。
