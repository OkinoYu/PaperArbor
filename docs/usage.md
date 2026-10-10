# 安装与两种交付方式

PaperArbor 不调用模型 API。用 Codex 加载 Skill 做研究和写作；Python 脚本处理缓存、渲染和校验。运行时网站无需 Python。维护需要 Python 3.9+；PDF 提图按需安装 PyMuPDF/Pillow（`python3 -m pip install pymupdf pillow`），未安装时仍可使用已核实的图或只用 SVG。

## 安装

```sh
git clone https://github.com/OkinoYu/PaperArbor.git
cd PaperArbor
```

在此目录打开 Codex，仓库 `.agents/skills/paper-arbor/SKILL.md` 可直接发现。若要在其他项目使用，把完整工具仓库保留在固定位置，然后在 Codex Skill 目录建立链接：

```sh
mkdir -p ~/.codex/skills
ln -s /absolute/path/PaperArbor/.agents/skills/paper-arbor ~/.codex/skills/paper-arbor
```

目标已存在时先检查，勿强制覆盖。也可直接在提示中给 Skill 的绝对路径。只复制 SKILL.md 会丢失 references 与脚本；这是有工具仓库依赖的 Skill。其他 agent 可显式读取相同 Skill 文件，但自动发现与权限取决于各自客户端。

## 独立 HTML

在任何工作区调用：

```text
$paper-arbor Single 精读 /path/paper.pdf，Standalone，只交付离线 HTML 与证据清单，输出到 /path/notes/。
$paper-arbor Series 梳理这些论文，Standalone，保留每代训练与推理的差异：……
```

Agent 核实论文后提供 `body.html`、`entry.json` 和 `evidence.json`；entry 的 sources 按 [metadata.md](metadata.md) 保留版本与 locator 对应。entry 不会自动加入 catalog。工具命令从 PaperArbor 根目录运行：

```sh
python3 scripts/render_article.py /path/notes/body.html --entry /path/notes/entry.json --evidence /path/notes/evidence.json --standalone -o /path/notes/draft.html
python3 scripts/embed_images.py /path/notes/draft.html -o /path/notes/paper.html
python3 scripts/validate_site.py --article /path/notes/paper.html --entry /path/notes/entry.json --evidence /path/notes/evidence.json --json
```

生成器不覆盖已有输出。最终 HTML 内嵌图、CSS、JS、MathML 和完整证据；断网不影响正文与查证。原文外链仍需联网。正文请用内部 fragment 和 HTTPS 原始来源，不引用 catalog/本地文件；单文件验证会拒绝文件依赖。Evidence JSON 随文件交付，供独立审阅。

## 知识库维护

```text
$paper-arbor Single 精读这篇论文，加入当前 PaperArbor，先只保留本地。
$paper-arbor Series 修订当前系列文章，保留原路径与收录日期，先只保留本地。
```

按同样的渲染命令去掉 `--standalone`，再发布到本地：

```sh
python3 scripts/publish_entry.py work/NAME/entry.json --html work/NAME/paper.html --evidence work/NAME/evidence.json --dry-run
python3 scripts/publish_entry.py work/NAME/entry.json --html work/NAME/paper.html --evidence work/NAME/evidence.json
python3 scripts/build_index.py --check
python3 scripts/validate_site.py --json
```

修订两条 publish 命令都加 `--replace`，保留 id/path/evidence/added。publisher 一起更新 article/evidence/catalog/index，使用锁、逐文件原子写与异常回滚，不是 crash-safe 多文件数据库。

本仓库已有用户的在线交付偏好，详见 AGENTS.md；外部用户不要照搬为自己的发布授权。`publish_entry.py` 只写本地；远程推送与 hosting 必须遵循当前用户指令。

## 可重复生成对照案例

QwenVL 的可维护正文保存在 `articles/qwenvl-series/body.html`，图像已内嵌；来源与 evidence 分别由 catalog 和 JSON 维护。运行：

```sh
python3 scripts/render_article.py articles/qwenvl-series/body.html --entry-id qwenvl-series --subtitle 'Qwen-VL → Qwen3.5 · 四篇原始报告与固定版本官方资料' -o work/qwenvl-preview.html
```

OPLD 的对应命令：

```sh
python3 scripts/render_article.py articles/opld-2607.28154/body.html --entry-id opld-2607.28154 --subtitle '先沿一道形状题走通方法，再分清向量反馈、教师参照与学生路径评分 · arXiv:2607.28154v1' -o work/opld-preview.html
```

这些命令只生成候选文件。随后用 `publish_entry.py --replace` 做完整修订验证。正文变动若新增事实，先同步 ledger；改变样式不会自动改写其他已发表文章。OPLD 的可维护正文保存在 `articles/opld-2607.28154/body.html`；同样通过 catalog/evidence 重渲染。已有文章只在明确修订时迁移。

## 本地预览与验收

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_index.py --check
python3 scripts/validate_site.py --json
python3 -m http.server 8000
```

浏览器打开 `http://localhost:8000`。验证移动、桌面、键盘、引用、无 JS 和 `/PaperArbor/` 前缀；静态验收不能证明科学事实或 JS 运行无网络请求，仍需来源复核与浏览器检查。质量方法见 [Skill 的验收规范](../.agents/skills/paper-arbor/references/quality.md)。
