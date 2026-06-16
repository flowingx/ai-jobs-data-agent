# AI Jobs Market Data Analysis Agent

自然语言分析 2025-2026 AI 就业市场数据，基于 LangChain + SQLite + LLM。

## 功能

- 自然语言 SQL 查询（支持中英文）
- 双引擎：DeepSeek（云端）或本地 GPU（llama.cpp）
- 多种图表：柱状图、饼图、折线图、散点图
- AI 摘要生成
- 1,500 条真实 AI 岗位数据（Kaggle 来源）
- 8 个预置查询示例（直接执行，不依赖 LLM）
- SQL 防幻觉机制（OR 链截断、长度限制）

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境
cp .env.example .env
# 编辑 .env，填入 DeepSeek API Key

# 3. 初始化数据库
python3 scripts/init_db.py

# 4. 启动
streamlit run app.py
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

### DeepSeek（云端）- 默认

- 稳定，推荐用于演示
- 需要网络和 API Key
- Max tokens: 1024

### 本地 GPU（llama.cpp）- 可选

- 离线运行，数据保留在本地
- 需要 GPU 和本地服务器

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
├── AGENT.md              # 技术开发文档
├── LICENSE               # Apache 2.0
├── README.md             # 本文件
├── requirements.txt      # Python 依赖
├── app.py                # Streamlit Web UI
├── data/
│   ├── ai_jobs_market_2025_2026.csv
│   └── charts/
├── db/
│   ├── ai_jobs.db        # SQLite 数据库（可重新生成）
│   └── careers.db
└── scripts/
    ├── data_agent.py     # SQL Agent（带重试）
    └── init_db.py        # 数据导入
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
- 搜索时统一使用 `LOWER(col) LIKE LOWER('%keyword%')` 忽略大小写

## License

Apache 2.0 - Copyright 2026 flowingx
