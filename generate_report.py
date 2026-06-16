import base64
import os
from pathlib import Path
from datetime import datetime

CHARTS_DIR = Path(__file__).parent / "data" / "charts"
OUTPUT = Path(__file__).parent / "report.html"


def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def generate_report():
    charts = {
        "skill_demand.png": ("技能需求排名", "统计各技能在岗位中出现的次数，Python、SQL、Docker 等基础技能需求最高。"),
        "skill_trends.png": ("技能趋势评分", "RAG、LLM API、Vector DB 等 AI 相关技能趋势得分最高，呈上升态势。"),
        "category_distribution.png": ("岗位类别分布", "互联网/AI 和开发/后端类岗位占比最大，数据和测试类也有一定需求。"),
        "province_jobs.png": ("各省市岗位分布", "北京、上海、广东岗位最多，一线城市求职机会集中。"),
        "salary_by_category.png": ("各类目平均薪资", "互联网/AI 类岗位平均薪资最高，运维/DevOps 类相对较低。"),
        "finance_distribution.png": ("公司融资阶段分布", "上市公司和不需要融资的企业占比较大，创业公司也有一定比例。"),
    }

    chart_html = ""
    for fname, (title, desc) in charts.items():
        fpath = CHARTS_DIR / fname
        if fpath.exists():
            b64 = img_to_base64(fpath)
            chart_html += f"""
            <div class="chart-card">
                <h3>{title}</h3>
                <img src="data:image/png;base64,{b64}" alt="{title}">
                <p class="chart-desc">{desc}</p>
            </div>
            """

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>实验7 - 数据分析智能体 实验报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f5f7fa; color: #333; line-height: 1.8; }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 40px 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 40px; border-radius: 16px; margin-bottom: 40px; text-align: center; }}
        .header h1 {{ font-size: 2.2em; margin-bottom: 10px; }}
        .header .subtitle {{ font-size: 1.1em; opacity: 0.9; }}
        .header .meta {{ margin-top: 20px; font-size: 0.9em; opacity: 0.8; }}
        .section {{ background: white; border-radius: 12px; padding: 30px; margin-bottom: 30px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
        .section h2 {{ color: #667eea; font-size: 1.5em; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }}
        .section h3 {{ color: #555; margin: 20px 0 10px; }}
        p {{ margin-bottom: 12px; }}
        ul, ol {{ margin: 10px 0 10px 20px; }}
        li {{ margin-bottom: 6px; }}
        .tech-stack {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 20px 0; }}
        .tech-item {{ background: #f0f4ff; padding: 16px; border-radius: 8px; text-align: center; }}
        .tech-item .name {{ font-weight: bold; color: #667eea; }}
        .tech-item .desc {{ font-size: 0.85em; color: #666; margin-top: 4px; }}
        .chart-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 24px; margin: 20px 0; }}
        .chart-card {{ background: #fafbfc; border-radius: 10px; padding: 20px; border: 1px solid #e8ecf1; }}
        .chart-card h3 {{ color: #333; margin-bottom: 12px; font-size: 1.1em; }}
        .chart-card img {{ width: 100%; border-radius: 6px; }}
        .chart-desc {{ color: #666; font-size: 0.9em; margin-top: 10px; }}
        pre {{ background: #1e1e1e; color: #d4d4d4; padding: 20px; border-radius: 8px; overflow-x: auto; font-size: 0.85em; line-height: 1.6; margin: 15px 0; }}
        code {{ font-family: "Fira Code", "Consolas", monospace; }}
        .inline-code {{ background: #eef; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; color: #c7254e; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #e8ecf1; }}
        th {{ background: #667eea; color: white; font-weight: 500; }}
        tr:hover {{ background: #f8f9ff; }}
        .flow-diagram {{ background: #f8f9ff; border: 2px solid #667eea; border-radius: 10px; padding: 30px; text-align: center; margin: 20px 0; font-size: 1.1em; }}
        .flow-step {{ display: inline-block; background: #667eea; color: white; padding: 8px 20px; border-radius: 20px; margin: 5px; }}
        .flow-arrow {{ display: inline-block; color: #667eea; font-size: 1.5em; margin: 0 5px; }}
        .footer {{ text-align: center; color: #999; padding: 30px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>实验7 - 数据分析智能体</h1>
            <div class="subtitle">基于 LangChain + SQLite + llama.cpp 的求职市场数据分析智能体</div>
            <div class="meta">数据库系统原理 | 2025-2026 春季学期 | {now}</div>
        </div>

        <div class="section">
            <h2>一、项目概述</h2>
            <p>本项目实现了一个基于 LangChain + SQLite + LLM 的求职市场数据分析智能体（Data Agent）。</p>
            <p>核心功能：</p>
            <ul>
                <li>自然语言问题理解与 SQL 自动生成</li>
                <li>SQLite 关系数据库查询（岗位信息、技能需求、薪资数据）</li>
                <li>查询结果的自然语言分析与解释</li>
                <li>求职市场数据可视化</li>
                <li>Streamlit 交互式 Web 界面</li>
            </ul>
        </div>

        <div class="section">
            <h2>二、技术架构</h2>
            <div class="flow-diagram">
                <span class="flow-step">用户输入</span>
                <span class="flow-arrow">&rarr;</span>
                <span class="flow-step">LangChain Agent</span>
                <span class="flow-arrow">&rarr;</span>
                <span class="flow-step">LLM (Qwen3-4B)</span>
                <span class="flow-arrow">&rarr;</span>
                <span class="flow-step">SQL 生成</span>
                <span class="flow-arrow">&rarr;</span>
                <span class="flow-step">SQLite 执行</span>
                <span class="flow-arrow">&rarr;</span>
                <span class="flow-step">结果解释</span>
            </div>
            <div class="tech-stack">
                <div class="tech-item"><div class="name">Python 3.13</div><div class="desc">主要编程语言</div></div>
                <div class="tech-item"><div class="name">LangChain 1.3.7</div><div class="desc">AI 应用框架</div></div>
                <div class="tech-item"><div class="name">llama.cpp</div><div class="desc">本地 LLM 推理</div></div>
                <div class="tech-item"><div class="name">Qwen3-4B</div><div class="desc">大语言模型</div></div>
                <div class="tech-item"><div class="name">SQLite</div><div class="desc">关系数据库</div></div>
                <div class="tech-item"><div class="name">Streamlit</div><div class="desc">Web 界面</div></div>
            </div>
        </div>

        <div class="section">
            <h2>三、数据库设计</h2>
            <p>基于原项目 career_data_agent.py 的数据库结构，包含 6 张表：</p>
            <table>
                <tr><th>表名</th><th>说明</th><th>记录数</th></tr>
                <tr><td><code class="inline-code">raw_jobs</code></td><td>岗位信息表</td><td>200</td></tr>
                <tr><td><code class="inline-code">job_skill_map</code></td><td>岗位-技能映射</td><td>~800</td></tr>
                <tr><td><code class="inline-code">project_templates</code></td><td>项目模板</td><td>5</td></tr>
                <tr><td><code class="inline-code">project_skill_map</code></td><td>项目-技能映射</td><td>~30</td></tr>
                <tr><td><code class="inline-code">learning_resources</code></td><td>学习资源</td><td>6</td></tr>
                <tr><td><code class="inline-code">skill_trends</code></td><td>技能趋势评分</td><td>12</td></tr>
            </table>
            <h3>建表 SQL</h3>
            <pre><code>CREATE TABLE raw_jobs (
    job_id INTEGER PRIMARY KEY,
    category TEXT,           -- 岗位大类
    sub_category TEXT,       -- 子类别
    job_title TEXT,          -- 职位名称
    province TEXT,           -- 省份
    job_location TEXT,       -- 城市
    job_company TEXT,        -- 公司
    job_industry TEXT,       -- 行业
    job_finance TEXT,        -- 融资阶段
    job_scale TEXT,          -- 公司规模
    job_salary_range TEXT,   -- 薪资范围
    job_experience TEXT,     -- 经验要求
    job_education TEXT,      -- 学历要求
    job_skills TEXT,         -- 技能要求
    salary_floor_k REAL     -- 薪资下限(K)
);

CREATE TABLE job_skill_map (
    job_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES raw_jobs(job_id)
);</code></pre>
        </div>

        <div class="section">
            <h2>四、Data Agent 实现</h2>
            <pre><code>from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="local-model",
    base_url="http://localhost:8080/v1",
    api_key="not-needed",
    temperature=0,
)

db = SQLDatabase.from_uri("sqlite:///db/careers.db")
agent = create_sql_agent(llm=llm, db=db, agent_type="openai-tools")

result = agent.invoke({{"input": "哪些技能在求职市场上最热门？"}})</code></pre>

            <h3>测试用例</h3>
            <table>
                <tr><th>问题</th><th>生成的SQL</th><th>结果</th></tr>
                <tr>
                    <td>哪些技能最热门？</td>
                    <td><code>SELECT skill FROM skill_trends ORDER BY trend_score DESC LIMIT 10</code></td>
                    <td>RAG(95), LLM API(91), Vector DB(88)</td>
                </tr>
                <tr>
                    <td>北京有哪些AI岗位？</td>
                    <td><code>SELECT * FROM raw_jobs WHERE province='北京' AND category='互联网/AI'</code></td>
                    <td>返回匹配的岗位列表</td>
                </tr>
                <tr>
                    <td>薪资最高的10个岗位？</td>
                    <td><code>SELECT job_title, salary_floor_k FROM raw_jobs ORDER BY salary_floor_k DESC LIMIT 10</code></td>
                    <td>返回高薪岗位</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h2>五、可视化展示</h2>
            <div class="chart-grid">
                {chart_html}
            </div>
        </div>

        <div class="section">
            <h2>六、Streamlit 界面</h2>
            <ul>
                <li><strong>智能查询</strong>：输入自然语言问题，Agent 自动生成 SQL 并返回分析结论</li>
                <li><strong>数据浏览</strong>：查看数据库各表结构和数据</li>
                <li><strong>预设分析</strong>：市场热度、地域分布、薪资分析、公司分析、技能匹配 5 大场景</li>
            </ul>
        </div>

        <div class="section">
            <h2>七、运行环境</h2>
            <table>
                <tr><th>组件</th><th>版本</th></tr>
                <tr><td>Python</td><td>3.13</td></tr>
                <tr><td>GPU</td><td>RTX 4060 Laptop (16GB)</td></tr>
                <tr><td>LLM</td><td>llama.cpp + Qwen3-4B Q4_K_M</td></tr>
                <tr><td>LangChain</td><td>1.3.7</td></tr>
                <tr><td>SQLite</td><td>内置</td></tr>
                <tr><td>Streamlit</td><td>1.58.0</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>八、大模型使用说明</h2>
            <p>使用 Qwen3-4B 本地模型，通过 llama.cpp 部署。</p>
            <table>
                <tr><th>使用场景</th><th>模型作用</th></tr>
                <tr><td>自然语言问题理解</td><td>理解用户输入的中文问题</td></tr>
                <tr><td>SQL 生成</td><td>根据 Schema 生成正确的 SQL</td></tr>
                <tr><td>SQL 检查</td><td>验证 SQL 语法正确性</td></tr>
                <tr><td>结果解释</td><td>将查询结果转化为分析结论</td></tr>
            </table>
        </div>

        <div class="footer">
            <p>实验7 - 数据分析智能体 | 数据库系统原理 2025-2026</p>
            <p>AI Jobs Market Data Analysis Agent | {now}</p>
        </div>
    </div>
</body>
</html>"""

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report: {OUTPUT} ({os.path.getsize(OUTPUT)/1024:.1f}KB)")


if __name__ == "__main__":
    generate_report()
