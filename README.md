# AI Jobs Market Data Analysis Agent

自然语言分析 2025-2026 AI 就业市场数据，基于 LangChain + SQLite + LLM。

## 功能

- 自然语言 SQL 查询（支持中英文）
- 双引擎：DeepSeek（云端）或本地 GPU（llama.cpp）
- 自动可视化（柱状图/饼图）
- AI 摘要生成
- 1,500 条真实 AI 岗位数据（Kaggle 来源）

## 快速开始

```bash
cd data_agent_project

# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境
cp .env.example .env
# 编辑 .env，填入 DeepSeek API Key

# 3. 初始化数据库
python3 scripts/init_db.py

# 4. 启动 Web UI
streamlit run app.py
```

打开 `http://localhost:8501`。

## 详细文档

- [data_agent_project/README.md](data_agent_project/README.md) — 完整使用说明
- [data_agent_project/AGENT.md](data_agent_project/AGENT.md) — 技术开发文档

## License

Apache-2.0
