# ContentFlow AI

ContentFlow AI 是一个面向内容创作流程的 AI 应用 MVP。当前仓库处于工程初始化阶段，业务节点尚未实现。

## 本地启动

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m contentflow
```

## 验证

```bash
pytest
ruff check .
```

## 目录

- `src/contentflow/`：应用代码
- `tests/`：自动化测试
- `docs/`：产品、架构和数据流设计文档
- `tools/`：文档和开发辅助脚本

配置从环境变量读取，复制 `.env.example` 为 `.env` 后再补充本地配置。`.env` 已被 Git 忽略，真实 API Key 不能进入代码、文档或 Commit。

## DeepSeek 连通性检查

将 DeepSeek Key 只保存于本机 `.env`，然后运行：

```bash
python -m contentflow.deepseek_hello
```

该命令只发送一条固定测试文本，不会运行 Planner、Writer 或其他业务流程。

