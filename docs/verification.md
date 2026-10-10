# 初版验收记录

验收日期：2026-10-10（Asia/Singapore）。本地实现与公开仓库发布完成，GitHub Pages 已启用；没有执行论文模型训练。

| 检查 | 结果 |
|---|---|
| `python3 -m unittest discover -s tests -v` | **37 tests passed**，系统 Python 3.9；无第三方测试依赖 |
| `python3 scripts/build_index.py --check` | 通过；索引与唯一目录清单一致 |
| `python3 scripts/validate_site.py --json` | 通过；2 个正式 HTML，5 张嵌入图，无站内断链/坏锚点 |
| 官方 Skill `quick_validate.py` | `Skill is valid!`；PyYAML 仅安装在临时 QA 目录，不是项目依赖 |
| 新建文章候选/本地发布 | 完整候选整站验证通过，正文/清单/证据/首页同步；明确修订也通过 |
| 发布保护 | 重复、防覆盖、跨目录逃逸、符号链接逃逸、并发锁、坏候选和写入异常回滚测试通过 |
| 原始论文身份 | 四个固定版本 PDF 和 arXiv 元数据核实，SHA-256 保存在目录 sources |
| 示例证据 | 51 条 claim/locator/anchor；原始报告表格数字与消融设置逐项核对 |
| 原图裁切 | 五图视觉检查；修复过贴边裁切，保留架构标签/实验轴/色标 |
| MathML / SVG | 五条 MathML 说明式、四张内联 SVG；XML/标签检查通过，浏览器公式正常显示 |
| 桌面检查 | 1280px 视口，正文与目录无重叠；全部五图加载；未观察到脚本错误 |
| 手机检查 | 390×844 视口；首页和正文没有页面横向溢出；目录折叠、宽图/宽表在容器内滚动；公式可读 |
| 首页交互 | 搜索不区分大小写；组合 Series/Qwen/DEEPSTACK 找到文章；空结果、LLM 无结果、重置验证通过 |
| 项目子路径 | 临时 `/PaperArbor/` 别名下首页→文章→首页均成功，资源使用相对路径 |
| 自包含 | 正文零外部 stylesheet/script；五图 data:image，公式原生 MathML、图形内联 SVG；主站页面不请求 JSON |
| 实时来源脚本 | arXiv API 返回 HTTP 429；按 ID 主站 abs 降级成功，正确固定 `2409.12191v2` 和日期 |
| 实时 Radar | arXiv API 请求超时；返回非零并保存 `status: failed` / 实际查询 / 错误，没有伪造候选 |
| GitHub Pages | `main` / `/ (root)` 发布成功，强制 HTTPS；[线上首页](https://okinoyu.github.io/PaperArbor/)、搜索、论文跳转、返回首页均正常；五图加载，四张 SVG、五条 MathML 存在，控制台无错误 |

浏览器截图：[桌面首页](images/home-desktop.jpg)、[手机公式与正文](images/article-mobile.jpg)。截图不是自动化可复现测试替代品；关键行为和结构另有标准库测试。

## 实际覆盖与限制

完整真实产物是 Qwen-VL Series。Single、Digest、Radar 的触发、研究规范和共享发布流程已实现，但本次没有为它们各生成一篇完整真实内容；后续应增加模式实例来持续检验写作质量。Radar 的离线解析/日期/失败测试通过，实时完整发现受到 API 超时限制。

获取工具支持 arXiv ID/URL、唯一论文标题与本地 PDF；论文名搜索依赖 arXiv API，不覆盖所有出版商。网络错误的 ID 请求有主站 abs 降级；其他情况需要 Codex 浏览器核实。PDF 文本读取由 Codex 的 PDF 工具或可选依赖完成，脚本不伪装自动科学分析器。

外部论文链接在此次来源下载时可访问，站点校验器不定期请求外网，也不验证远程地址是否存在；Pages 上线由浏览器另行确认。单独拷走的 HTML 正文可离线阅读，但返回主页和单独 JSON ledger 链接需要整站目录；原文链接需要网络。没有模拟全系统断网，离线资源由结构检查和浏览器加载验证。

SVG/MathML 检查能发现结构和依赖错误，不能鉴别科学结论正确性。重要公式均标“说明式”，不是原文逐字抄录公式；Qwen3 loss 的精确实现不足以从报告中确认，因此没有补造。

项目原创部分 MIT；五张原论文图没有被重新授权为 MIT，文章和 README 明确保留出处与版权范围。发布器做每文件原子写入和异常回滚，不保证系统崩溃时的多文件事务一致性。

## 下一步

增加真正的 Single/Digest/Radar 范例；接入更多公开论文发现源；为实验协议与 claim 建立更细的结构化字段；随着真实使用改进 Skill 的研究深度与证据审阅。
