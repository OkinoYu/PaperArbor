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
