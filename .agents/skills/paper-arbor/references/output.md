# 网页与发布输出

使用仓库 `assets/article.css` / `article.js` 与 `scripts/render_article.py`；模板包含桌面目录、移动折叠目录、打印和阅读进度。body 是可信作者 HTML，不把未处理的用户字符串拼成 HTML。所有 h2 使用唯一 id，正文不再添加 h1。

关键结论用 `.callout`，编辑分析用 `.callout.analysis` 加“分析判断”标签，未知信息显式写“未公开/本次未核实”。表格包 `.table-wrap` 并包含 caption/表头。图片包 figure，alt 解释图意，figcaption 写论文、版本、Figure N、PDF 页码与裁切说明。

重要公式用原生 MathML，`<math xmlns="http://www.w3.org/1998/Math/MathML" display="block" aria-label="…">`；紧接中文解释和来源。没有外部公式运行时。现代浏览器支持；读屏标签保留可读表达。复杂公式可生成静态内联 SVG，但要保留文本说明。

SVG 内联，`xmlns`、viewBox、role="img"、aria-labelledby、title 与唯一 marker IDs 完整。用 `.viz-scroll` 容器使密集图在手机上横向滚动；切勿强缩导致无法阅读。解释性示意图标明重绘及依据，不将推导/预测冒充实验。宽表在容器内滚动，页面本身不能横向溢出。

图片最终使用合法 base64 data:image。脚本支持 PNG/JPEG/WebP/GIF/SVG 数据；不支持 srcset、多媒体/iframe/外部 CSS/JS/font 运行时。先下载并检查远程图，再用本地嵌入脚本；普通论文出处链接可以外部 HTTPS。

发布脚本检查全站副本、重复、防覆盖、local links/fragment、离线资源、SVG/MathML XML、清单和证据 anchor。这些是静态校验，不能确认实验数字科学正确或运行中的 JS 不请求网络；必须人工/agent 复核来源、视觉和离线行为。

## 渲染与证据交互

`render_article.py --entry entry.json --evidence evidence.json` 内嵌完整 ledger 与来源；`--entry-id ID` 从当前 catalog 读取同一记录和 evidence。h2 必须手写稳定 id，h3 自动获得所属 h2 下的确定性 id；长期链接建议手写 h3 id。不要使用布局保留 id（article/top/evidence-* 等）。

Standalone 加 `--standalone`，只生成内部跳转，不带 index/关联文件依赖；正文的外部文件链接仍须作者去除。Library 可带关联阅读，理由来自共享来源或标签。渲染不自动生成新的科学 claim。

完整 evidence 以安全 JSON 和静态列表同时保存在 HTML。JS 开启时可按章/来源过滤搜索，关闭 JS 时文末 details 内仍有全部 locator 与返回链接。引用链接保留 href，Ctrl/Command 沿原链接跳转；显式 PDF 链接直接打开原文，不拦截为查证窗口。外部 ledger 与嵌入内容必须一致，validator 会拒绝陈旧副本。

表格/SVG/公式建议作者给滚动容器 tabindex、role=region、aria-label；JS 也会增强这些属性。交互必须渐进增强，禁用 JS 时核心信息可读，按钮操作不能删除科学条件。

用户明确要求目录/方向迁移时，entry 登记旧路径 `aliases`，使用 `publish_entry.py --replace --move` 先 dry-run 再发布；保留 id/evidence/added。publisher 生成旧网址跳转并同步文章间链接，普通修订不使用此选项。方向和路径格式以 common.py 与 metadata.md 为准。
