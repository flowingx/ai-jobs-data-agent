# AI Jobs Market Data Analysis Agent

自然语言分析 2025-2026 AI 就业市场数据，基于 LangChain + SQLite + LLM。

## 功能

- 自然语言 SQL 查询（支持中英文）
- 双引擎：DeepSeek（云端）或本地 GPU（llama.cpp）
- 多种图表：柱状图、饼图、折线图、散点图
- AI 摘要生成
- 1,500 条真实 AI 岗位数据（Kaggle 来源）
- 8 个预置查询示例（直接执行，不依赖 LLM）
- SQL 防幻觉机制（只读校验、OR 链截断、长度限制）
- 高频展示问题使用确定性 SQL，避免远程岗位、技能年份对比等语义漂移

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境
cp .env.example .env
# 编辑 .env，填入 DeepSeek API Key

# 3. 初始化数据库
python scripts/init_db.py

# 4. 启动
streamlit run app.py

# 5. 测试
python -m unittest discover tests -v
```

打开 `http://localhost:8501`。

## 配置说明

1. 复制 `.env.example` 为 `.env`
2. 编辑 `.env`，填入你的 API Key：
   ```
   DEEPSEEK_API_KEY=sk-your-key-here
   ```
3. 获取 DeepSeek API Key: https://platform.deepseek.com/

## 双引擎配置

> 推荐使用云端大模型（DeepSeek）。本地小模型（如 4B）可能出现上下文窗口不足、SQL 生成质量差等问题。

### DeepSeek（云端）- 默认

- 稳定可靠，SQL 生成质量高
- 需要网络和 API Key
- Max tokens: 1024

### 本地 GPU（llama.cpp）- 可选

- 离线运行，数据保留在本地
- 需要 GPU 和本地服务器
- 注意：小模型上下文窗口有限，复杂查询可能失败

在另一个终端启动 GPU 服务器：

```bash
LD_LIBRARY_PATH=/usr/local/cuda-12.6/lib64:/tmp/llama-cuda-build/build/bin \
  /tmp/llama-cuda-build/build/bin/llama-server \
  --model ~/models/Qwen3VL-4B-Instruct-Q4_K_M.gguf \
  --mmproj ~/models/mmproj-Qwen3VL-4B-Instruct-Q8_0.gguf \
  --host 127.0.0.1 --port 8080 --ctx-size 4096 -ngl 99
```

然后在 UI 侧边栏选择 "Local GPU"。

## 命令行使用

```bash
# DeepSeek（默认）
python3 scripts/data_agent.py -q "What are the top 5 skills?"

# 本地 GPU
python3 scripts/data_agent.py -q "What are the top 5 skills?" -e local
```

## 项目结构

```
├── .env.example          # 环境配置模板
├── .gitignore
├── AGENTS.md             # AI Agent 工作指南
├── LICENSE               # Apache 2.0
├── README.md             # 本文件
├── requirements.txt      # Python 依赖
├── app.py                # Streamlit Web UI
├── data/
│   ├── ai_jobs_market_2025_2026.csv  # 课程提交包包含；缺失时可按下方命令下载
│   └── charts/
├── db/
│   └── ai_jobs.db        # SQLite 数据库（可重新生成）
├── scripts/
│   ├── __init__.py
│   ├── llm_utils.py      # 共享 LLM/SQL 工具函数
│   ├── data_agent.py     # CLI Agent（带重试）
│   └── init_db.py        # 数据导入
└── tests/
    ├── test_llm_utils.py        # LLM 输出解析、SQL 只读校验与高频问题 SQL
    ├── test_init_db.py          # 数据库初始化幂等性
    ├── test_execute_sql_safety.py # execute_sql 只读执行安全
    ├── test_docs_consistency.py # 文档一致性验证
    └── test_app_preset_queries.py # 预置查询、数据浏览查询与图表策略验证
```

## 数据库结构

| 表名 | 行数 | 说明 |
|------|------|------|
| job_postings | 1,500 | 岗位信息（薪资、技能、地点） |
| job_skills | 9,548 | 技能关联表（每行一个技能） |
| job_categories | 12 | 类别统计 |
| experience_levels | 4 | 经验要求统计 |
| location_summary | 20 | 地点统计 |

## 数据格式说明

- `job_skills.skill`：独立行存储（每行一个技能）
- `job_postings.required_skills`：管道符分隔（如 `Python|SQL|Cloud`）
- `job_postings.remote_work`：文本字段，取值为 `Fully Remote`、`Hybrid`、`On-site`
- 搜索时统一使用 `LOWER(col) LIKE LOWER('%keyword%')` 忽略大小写
- “远程 vs 现场”薪资对比中，`Fully Remote` 与 `Hybrid` 会归为 `Remote`，再与 `On-site` 对比

## 查询与安全策略

- 运行 SQL 前会先做只读校验，拒绝 `DROP`、`UPDATE`、`PRAGMA` 等危险语句。
- SQLite 执行连接使用只读 URI（`mode=ro`），并设置 `PRAGMA query_only=ON`。
- LLM 输出会先清洗 markdown、注释和 `<think>` 内容，再提取 SQL。
- CUDA/Python 年份对比、远程/现场平均薪资等课程展示高频问题使用确定性 SQL，减少模型生成差异。

## 数据集与提交包注意事项

- 课程提交包中包含 `data/ai_jobs_market_2025_2026.csv`，用于离线复现。
- 如果 CSV 缺失，可运行：
  ```bash
  kaggle datasets download -d alitaqishah/ai-jobs-market-2025-2026-salaries -p data --unzip
  ```
- `scripts/init_db.py` 默认检测到已有数据库后跳过重建；需要强制重建时运行：
  ```bash
  python scripts/init_db.py --force
  ```
- 打包 RAR 时不要包含 `.env`，只保留 `.env.example`，避免泄露 API Key。

## 最终提交清单

建议包含：
- 源码：`app.py`、`scripts/`、`tests/`
- 文档：`README.md`、`AGENTS.md`、`db/ER_DIAGRAM.md`
- 数据：`data/ai_jobs_market_2025_2026.csv`
- 报告：`实验报告_数据分析智能体.docx`
- 环境模板：`.env.example`

不要包含：
- `.env`
- `.venv/`、`venv/`
- `__pycache__/`
- 临时日志和 IDE 本地配置文件

## License

Apache 2.0 - Copyright 2026 flowingx
