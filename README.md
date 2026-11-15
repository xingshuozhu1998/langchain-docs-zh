# LangChain 官方文档中英对照阅读站

网站地址：<https://xingshuozhu1998.github.io/langchain-docs-zh/>。

本项目保存官方文档的中文译文与静态发布流程。英文来源为 [langchain-ai/docs 的 a09b855be 提交](https://github.com/langchain-ai/docs/commit/a09b855be906129eed995b9476897b7d1a618376)，对应本地中英对照版本 `6d2fbe808`，并包含 `3b834dd78` 中由 Luna 补齐的 LangChain 概览首段。原项目许可证保留在 `LICENSE`。

中文范围为 LangChain、LangGraph、Deep Agents，以及原有四篇概念文档；正文保留英文后接中文。本轮由 Luna 更新和复核 161 页，未变化的旧译文继续保留。只发布这一翻译范围，其他文档链接转到官方站；Python、TypeScript 和 Deep Agents Code 页面均保留。

## 构建和发布

`.github/workflows/pages.yml` 在推送到 `main` 或手动触发时构建并发布：

1. 下载固定的官方提交，将 `translations.patch.gz.b64` 解码、解压并应用，恢复中英对照源文件。
2. 安装官方构建依赖，使用 `docs build` 预处理页面，裁剪为已确认的翻译导航，并移除官方域名绑定的统计配置；再由固定版本 `mint@4.2.940`（客户端 `0.0.3697`） 导出静态 HTML。
3. `publish.py` 为 `/langchain-docs-zh/` 项目路径调整资源与导航，复用完全相同的内联脚本，并排除未被源文件或生成页面引用的历史素材。仅保留选定范围的导出页面，保留正在使用的图片及动画格式，不改英文原文或中文源文件。
4. 浏览器检查三个产品概览的中文正文、主题菜单、跨页跳转、手机布局和官方外链，检查通过后发布到 GitHub Pages。若最终大小达到 1 GB，构建失败，不发布超限产物。

静态站点使用完整 HTML 跳转。页内组件仍由 Mintlify 脚本运行。搜索、在线 AI 问答及需要服务器的 API 交互不属于纯静态托管能力；外部链接、视频和 API 参考仍依赖网络。

## 更新译文

在中英对照源仓库中重新生成补丁（`origin/main` 必须与工作流固定的官方提交一致）：

```bash
git diff origin/main HEAD -- src | gzip -n | base64 -w 0 > /path/to/langchain-docs-zh/translations.patch.gz.b64
```

如果同步新的官方版本，同时更新工作流中的提交号、译文补丁和本说明中的版本记录。补丁只是压缩的 Git 文本差异，不包含令牌或运行环境。

## 验证记录

源文档构建成功，481 项管道单元测试通过，161 页文字规范检查通过。原本存在的两条 TypeScript 集成失效链接及五项 Mintlify 组件检查警告记录在源仓库 `task.md` 中。

范围内导出页面共 335 个。精简导航后的最终本机产物为 611.5 MB，低于 1 GB 限制；最终自动构建仍检查产物体积。部署结果以 [Actions 工作流](https://github.com/xingshuozhu1998/langchain-docs-zh/actions) 为准。

本机部署代码位于 `/data/zhuxs/llm_agent/langchain-docs-zh`，中英对照源文档仍位于 `/data/zhuxs/llm_agent/docs`。线上阅读不需要启动本机进程。
