# Catalog and evidence contracts

`data/papers.json` is a JSON array. Required record fields:

```json
{
  "id": "example-2301.00001",
  "title": "Example 方法精读",
  "summary": "具体说明解决的问题与机制。",
  "category": "LLM",
  "type": "Single",
  "published": "2023-01-01",
  "added": "2026-10-10",
  "path": "examples/LLM/example-2301.00001.html",
  "tags": ["Attention"],
  "sources": [{
    "id": "2301.00001v1",
    "title": "Verified original title",
    "authors": "Verified complete author list",
    "url": "https://arxiv.org/abs/2301.00001v1",
    "version": "v1",
    "published": "2023-01-01"
  }],
  "evidence": "data/evidence/example-2301.00001.json"
}
```

This is a schema example, not a real scientific record. `published` is paper first-submission date; a Series/Digest uses the latest included paper first-submission date, with full per-paper dates under sources. Radar uses report interval end. `added` is catalog entry date in the user's local timezone. Optional source fields include version date, SHA-256, author project links. Entry IDs/paths and same-mode canonical source sets must be unique; different modes may discuss the same source. Paths must remain inside the site and articles must live under their category.

Evidence ledger:

```json
{
  "reviewed": "2026-10-10",
  "coverage": "Full versioned PDFs; unavailable items explicitly described",
  "claims": [{
    "anchor": "method",
    "source": "2301.00001v1",
    "locator": "Section 3.2, Figure 2, PDF page 4",
    "statement": "The specific fact being supported",
    "kind": "paper-fact"
  }]
}
```

`kind` may be `paper-fact`, `explanatory-derivation`, `editorial-analysis` or `figure`. Repeat claims when one section has several important numbers or mechanisms. For a numerical table row preserve checkpoint, task/split, metric, precision, and direction in statement or additional fields. Anchor must exist in HTML. Source ID must match the article's versioned sources. Caption citations remain visible even if this ledger is not downloaded. The ledger enables review; automated existence checks cannot authenticate scientific facts.

For a Radar report with no verified papers, retain an explicit discovery source (`kind: "discovery-feed"`) with the actual HTTPS query URL, stable query/interval ID, publisher in `authors` (e.g. arXiv), retrieval timestamp in `version`, and interval end in `published`. These fields identify the feed, not a fictional paper. Record failed/empty/truncated status in the ledger coverage and visible report.

## 可维护正文与内嵌证据

可选 entry 字段 `updated` 为最后有意修订日期（不得早于 added），`body` 为 `articles/<stem>/body.html` 的作者正文路径。渲染器不改写正文；长期引用请手写 h3/h4 id，自动 h3 id 仅作确定性补全。修订仍保留原 id/path/evidence/added。源码可内嵌已选定图，原始 PDF/裁切中间文件仍在忽略目录。

source 的可选 `sha256`、`config_sha256` 等 `*sha256` 字段必须是 64 位小写十六进制，指对应实际字节，不能以哈希替代版本核实。校验器检查格式，不重新下载原文比对。

传 entry/evidence 渲染时，HTML 保存 `evidence-data` 安全 JSON 和可展开的静态证据列表。新增 Library 产物的嵌入来源/ledger 与外部清单必须相等；旧产物可按有意修订逐步迁移。Standalone 的 `--article` 检查要求内嵌证据，并拒绝对 catalog 或其他本地文件的链接依赖；不必提供完整站点。

关联阅读从共同规范 source ID（去 arXiv 版本号）或相同 tag 生成，显示关联理由。标签只用于发现，不能证明论文有继承关系。

## 方向与旧地址

支持 LLM、VLM、Multimodal、Reasoning、Agent、RL、OPD、Others。`category` 与 canonical `path` 的目录匹配；首页按钮与方向总数从同一个 CATEGORIES 集合生成。

可选 `aliases` 是旧文章路径数组，例如 `examples/VLM/opld-2607.28154.html`。它们只保留指向当前 canonical path 的跳转，不增加论文记录或计数；与所有 article/alias 路径全局去重。迁移必须由用户明确要求，使用 publisher `--replace --move`，保留原 id/evidence/added，并把旧 canonical path 加入 aliases。publisher 同时生成旧地址页、改写站内文章链接和首页，异常时回滚；校验器验证 alias 的目标，普通修订仍拒绝改路径。
