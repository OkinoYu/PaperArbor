# 网页与发布输出

使用仓库 `assets/article.css` / `article.js` 与 `scripts/render_article.py`；模板包含桌面目录、移动折叠目录、打印和阅读进度。body 是可信作者 HTML，不把未处理的用户字符串拼成 HTML。所有 h2 使用唯一 id，正文不再添加 h1。

关键结论用 `.callout`，编辑分析用 `.callout.analysis` 加“分析判断”标签，未知信息显式写“未公开/本次未核实”。表格包 `.table-wrap` 并包含 caption/表头。图片包 figure，alt 解释图意，figcaption 写论文、版本、Figure N、PDF 页码与裁切说明。

重要公式用原生 MathML，`<math xmlns="http://www.w3.org/1998/Math/MathML" display="block" aria-label="…">`；紧接中文解释和来源。没有外部公式运行时。现代浏览器支持；读屏标签保留可读表达。复杂公式可生成静态内联 SVG，但要保留文本说明。

SVG 内联，`xmlns`、viewBox、role="img"、aria-labelledby、title 与唯一 marker IDs 完整。用 `.viz-scroll` 容器使密集图在手机上横向滚动；切勿强缩导致无法阅读。解释性示意图标明重绘及依据，不将推导/预测冒充实验。宽表在容器内滚动，页面本身不能横向溢出。

图片最终使用合法 base64 data:image。脚本支持 PNG/JPEG/WebP/GIF/SVG 数据；不支持 srcset、多媒体/iframe/外部 CSS/JS/font 运行时。先下载并检查远程图，再用本地嵌入脚本；普通论文出处链接可以外部 HTTPS。

发布脚本检查全站副本、重复、防覆盖、local links/fragment、离线资源、SVG/MathML XML、清单和证据 anchor。这些是静态校验，不能确认实验数字科学正确或运行中的 JS 不请求网络；必须人工/agent 复核来源、视觉和离线行为。
