# PaperArbor engineering conventions

PaperArbor is an AI-Powered Visual Research Knowledge Base: **Where Papers Grow into Knowledge.**
Read this file before editing. Honor explicit user scope; never create a repository, push, or enable hosting without an instruction.

## Delivery preference

The user reads this project at https://okinoyu.github.io/PaperArbor/ and has requested online delivery. For completed paper additions and intended revisions, commit the article, evidence, catalog and generated index together, push to the existing `origin/main` after the required checks, and verify the live Pages result. This standing instruction authorizes those routine updates; it does not authorize creating repositories or changing hosting settings. Honor any later request to keep work local.

## Architecture

- Native HTML/CSS/JS static site, Python 3.9+ standard-library maintenance. No Node, database or backend required.
- `data/papers.json` is the sole catalog source; `templates/index.html` plus `scripts/build_index.py` produce `index.html`.
- `assets/style.css`/`app.js` serve the homepage. `article.css`/`article.js` are inlined by `render_article.py`; existing articles change only through intended revisions.
- Agent authors verified Chinese HTML body, metadata entry and evidence ledger; deterministic scripts fetch, render, publish and validate. Scripts do not automatically perform scientific reasoning.
- `examples/<Category>/*.html` are independently readable files. `data/evidence/*.json` retain claims and source locators. Original paper downloads/crops belong in ignored `work/` or a temporary directory.
- `.agents/skills/paper-arbor/SKILL.md` is the repository-native Codex skill, called with `$paper-arbor`. Read its selected mode reference when using it. Run commands from the repository root; avoid duplicating scripts inside the skill.

## Research quality

Verify identities and versioned primary papers before drafting. Read methods, training, inference, main experiments and ablations, not only abstracts. For each critical module explain input, transformation, output, supervision, reason and limitations. Adapt eleven suggested chapters to the paper; explicitly mark absent evidence rather than fabricate it. Series must explain inherited/replaced mechanisms, not concatenate summaries. Digest compares assumptions and evaluation protocols. Radar is one-shot discovery with explicit dates and source failure/coverage status.

Every experimental number, parameter count, formula and chart must have a nearby citation with section/table/figure/page and a claim in the evidence ledger. Preserve units, precision, evaluation split, checkpoint and inference mode. Derived formulas/deltas are labeled as explanatory derivations; author's claims, editorial analysis, and unknowns are distinguished. Do not infer causality from release-to-release benchmarks or mix pairs, samples and tokens. Never copy another site's generated analysis. A failed download is not evidence of zero papers or zero capability.

## Design and naming

Use warm paper, forest green, restrained amber, readable Chinese text and clear section hierarchy. Desktop sticky TOC; mobile collapsible TOC and scrollable wide tables/SVGs. Include source captions, alt text, a skip link, keyboard focus and reduced-motion support. No remote fonts/runtime scripts. MathML with `aria-label` renders important equations offline; follow each with Chinese symbol explanations and a source. Inline SVG requires `viewBox`, `role="img"`, `aria-labelledby` and a `<title>`; arrows show real data flow. No raw LaTeX delimiters, fabricated quantitative graphics or decorative equations.

Choose stable ASCII stems: `<paper-name>-<arxiv-id>.html`, `<family>-series.html`, `<topic>-<date>-digest.html`, `<topic>-<start>-<end>-radar.html`. Legacy first example is `examples/VLM/QwenVL-series.html`. Categories: LLM, VLM, Multimodal, Reasoning, Agent, RL, Others. Source IDs include verified versions; de-duplicate same-mode canonical source sets, IDs and case-insensitive paths. Single and Series may intentionally share a source.

## Figures

Prefer load-bearing original figures plus explanatory SVGs. `extract_figure.py --page` uses 1-based PDF page numbers; crop boxes use `(x0, top, x1, bottom)` in PDF points. Preserve labels, panel boundaries and legend, inspect the crop visually. Lossless PNG for diagrams, JPEG/WebP may suit photos. Usually 1200–1600 px width, target ≤350 KB; preserve legibility over an arbitrary size target and document exceptions. Embed final raster figures as base64. `srcset` is deliberately unsupported: use one compressed image. Credit the source and identify any crop/redrawing. Article code MIT does not relicense embedded paper figures; record attribution and redistribution conditions.

## Update process

1. Resolve and verify sources in an ignored work directory.
2. Author body HTML plus a metadata entry (`docs/metadata.md`) and evidence ledger.
3. Render into a new staging path and embed local images; never overwrite another article to get a draft.
4. `publish_entry.py entry.json --html draft.html --evidence evidence.json --dry-run` validates a full temporary site.
5. Publish with the same command without `--dry-run`. Default refuses existing files/records. Use `--replace` only for an intended revision; retain original added date and paths.
6. Run `build_index.py --check`, `validate_site.py`, and relevant tests. Inspect desktop/mobile and disconnected article rendering when browser tools are available.
7. Report paths, evidence gaps and checks. No automatic external publication.

Publisher uses an exclusive lock, per-file atomic writes and exception rollback. It is not a crash-safe multi-file database transaction. After process termination, inspect `.publish.lock` and site consistency before manually removing a stale lock. Do not change data concurrently with publishing.

## Checks and release

`python3 -m unittest discover -s tests -v`, `python3 scripts/build_index.py --check`, `python3 scripts/validate_site.py --json` are release checks. Validate fetch/radar parsing with offline fixtures; optional live HTTP failures must be reported, not hidden. Validator checks paths, fragments, catalog freshness, inline XML, asset containment and evidence anchors; human/agent source review remains essential and is not replaced by syntactic checks. External URLs are not fetched by the site validator.

Use relative links (`../../index.html` from category articles); no root-absolute `/assets` or `/examples` links. Preview with `python3 -m http.server 8000`, and test a `/PaperArbor/` prefix. GitHub Pages may serve `main` `/ (root)` without server Python. Commit generated index/article together with metadata. Keep caches, PDFs, secrets and browser screenshots out of releases unless intentionally selected.
