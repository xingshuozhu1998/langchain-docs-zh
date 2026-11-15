# LangChain 官方文档中英对照阅读站

网站地址：<https://xingshuozhu1998.github.io/langchain-docs-zh/>。

本项目保存官方文档的中文译文与静态发布流程。英文来源为 [langchain-ai/docs 的 a09b855be 提交](https://github.com/langchain-ai/docs/commit/a09b855be906129eed995b9476897b7d1a618376)，对应本地中英对照版本 `6d2fbe808`。原项目许可证保留在 `LICENSE`。

中文范围为 LangChain、LangGraph、Deep Agents，以及原有四篇概念文档；正文保留英文后接中文。本轮由 Luna 更新和复核 161 页，未变化的旧译文继续保留。其他官方页面保持英文。当前已完成官方导航全量静态导出的验证；最终发布范围等待确认。

## 构建和发布

自动部署工作流草案暂保存在本地 `.github/workflows/pages.yml`，确认发布范围后提交。设计流程如下：

1. 下载固定的官方提交，将 `translations.patch.gz.b64` 解码、解压并应用，恢复中英对照源文件。
2. 安装官方构建依赖，使用 `docs build` 预处理页面，再由固定版本 `mint@4.2.940`（客户端 `0.0.3697`） 导出静态 HTML。
3. `publish.py` 为 `/langchain-docs-zh/` 项目路径调整资源与导航，复用完全相同的内联脚本，并排除未被源文件或生成页面引用的历史素材。保留全部导出页面，保留正在使用的图片及动画格式，不改英文原文或中文源文件。
4. 发布到 GitHub Pages。若最终大小达到 1 GB，构建失败，不发布超限产物。

静态站点使用完整 HTML 跳转。页内组件仍由 Mintlify 脚本运行。搜索、在线 AI 问答及需要服务器的 API 交互不属于纯静态托管能力；外部链接、视频和 API 参考仍依赖网络。

## 更新译文

在中英对照源仓库中重新生成补丁（`origin/main` 必须与工作流固定的官方提交一致）：

```bash
git diff origin/main HEAD -- src | gzip -n | base64 -w 0 > /path/to/langchain-docs-zh/translations.patch.gz.b64
```

如果同步新的官方版本，同时更新工作流中的提交号、译文补丁和本说明中的版本记录。补丁只是压缩的 Git 文本差异，不包含令牌或运行环境。

## 验证记录

源文档构建成功，481 项管道单元测试通过，161 页文字规范检查通过。原本存在的两条 TypeScript 集成失效链接及五项 Mintlify 组件检查警告记录在源仓库 `task.md` 中。

当前尚未发布。完整导出经过素材整理和重复脚本复用后仍约 1.21 GB，超过 Pages 的 1 GB 上限；发布范围等待确认。子目录下的主题菜单和页面跳转已通过本地浏览器检查，线上结果将在完成发布后补充。
