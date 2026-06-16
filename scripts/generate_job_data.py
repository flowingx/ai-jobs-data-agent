import random
import sqlite3
from pathlib import Path

import pandas as pd

DB_DIR = Path(__file__).parent.parent / "db"
DB_PATH = DB_DIR / "careers.db"

CATEGORIES = {
    "互联网/AI": {
        "sub_categories": ["AI应用", "大模型", "Agent", "工程化", "NLP", "CV"],
        "industries": ["人工智能", "企业服务", "云计算", "大数据"],
    },
    "开发/后端": {
        "sub_categories": ["Python", "Java", "Go", "Node.js", "C++"],
        "industries": ["SaaS", "电商", "金融", "游戏", "社交"],
    },
    "开发/前端": {
        "sub_categories": ["React", "Vue", "小程序", "跨端"],
        "industries": ["电商", "教育", "医疗", "金融"],
    },
    "数据": {
        "sub_categories": ["数据分析", "数据工程", "数据仓库", "BI"],
        "industries": ["电商", "金融", "广告", "游戏"],
    },
    "测试": {
        "sub_categories": ["自动化测试", "测试开发", "性能测试"],
        "industries": ["金融", "电商", "游戏", "教育"],
    },
    "运维/DevOps": {
        "sub_categories": ["运维开发", "SRE", "云原生"],
        "industries": ["云计算", "金融", "电商"],
    },
}

COMPANIES = [
    "星河智能科技", "澜舟数据", "云杉科技", "青禾电商", "北辰智算", "数桥云",
    "蓝鲸信息", "飞书科技", "字节跳动", "阿里巴巴", "腾讯", "美团",
    "京东", "网易", "百度", "快手", "小红书", "B站", "滴滴", "拼多多",
    "华为", "小米", "OPPO", "vivo", "大疆", "商汤", "旷视", "第四范式",
    "地平线", "寒武纪", "智谱AI", "月之暗面", "MiniMax", "零一万物",
    "深势科技", "光年之外", "面壁智能", "阶跃星辰", "百川智能", "昆仑万维",
]

PROVINCES = {
    "北京": ["北京"],
    "上海": ["上海"],
    "广东": ["深圳", "广州", "东莞"],
    "浙江": ["杭州", "宁波", "温州"],
    "江苏": ["南京", "苏州", "无锡"],
    "四川": ["成都"],
    "湖北": ["武汉"],
    "福建": ["厦门", "福州"],
    "陕西": ["西安"],
    "安徽": ["合肥"],
}

FINANCE_ROUNDS = ["天使轮", "A轮", "B轮", "C轮", "D轮", "上市公司", "不需要融资", "已上市"]

SCALES = ["0-20人", "20-49人", "50-99人", "100-499人", "500-999人", "1000-9999人", "10000人以上"]

EXPERIENCES = ["在校/应届", "1-3年", "3-5年", "5-10年", "不限"]

EDUCATIONS = ["大专", "本科", "硕士", "博士", "不限"]

SKILL_POOL = {
    "语言": ["Python", "Java", "Go", "JavaScript", "TypeScript", "C++", "Rust", "SQL"],
    "框架": ["FastAPI", "Django", "Flask", "Spring", "Express", "React", "Vue", "Next.js"],
    "AI": ["LangChain", "LangGraph", "RAG", "LLM API", "Prompt Engineering", "Fine-tuning", "PyTorch", "TensorFlow"],
    "数据": ["pandas", "NumPy", "Spark", "Flink", "Kafka", "Hive", "ClickHouse"],
    "数据库": ["MySQL", "PostgreSQL", "Redis", "MongoDB", "Elasticsearch", "Milvus"],
    "DevOps": ["Docker", "Kubernetes", "AWS", "Azure", "CI/CD", "Terraform"],
    "工具": ["Git", "Linux", "Shell", "Jira", "Confluence"],
}

ALL_SKILLS = []
for skills in SKILL_POOL.values():
    ALL_SKILLS.extend(skills)


def random_salary_floor(salary_range: str) -> float:
    import re
    text = salary_range.lower()
    month = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*k", text)
    if month:
        return float(month.group(1))
    day = re.search(r"(\d+)\s*-\s*(\d+)\s*元/天", text)
    if day:
        return round(float(day.group(1)) * 21 / 1000, 1)
    return None


def generate_skills(category: str, sub_category: str) -> str:
    n = random.randint(3, 7)
    skills = random.sample(ALL_SKILLS, min(n, len(ALL_SKILLS)))
    return ", ".join(skills)


def generate_salary(category: str) -> str:
    base = random.choice([10, 12, 15, 18, 20, 25, 30, 35, 40])
    top = base + random.randint(5, 15)
    return f"{base}-{top}K"


def generate_jobs(n: int = 200) -> list[dict]:
    jobs = []
    for i in range(n):
        category = random.choice(list(CATEGORIES.keys()))
        cat_info = CATEGORIES[category]
        sub_category = random.choice(cat_info["sub_categories"])
        industry = random.choice(cat_info["industries"])

        province = random.choice(list(PROVINCES.keys()))
        city = random.choice(PROVINCES[province])

        company = random.choice(COMPANIES)
        finance = random.choice(FINANCE_ROUNDS)
        scale = random.choice(SCALES)
        experience = random.choices(EXPERIENCES, weights=[15, 40, 30, 10, 5])[0]
        education = random.choices(EDUCATIONS, weights=[5, 50, 35, 5, 5])[0]

        title_map = {
            "互联网/AI": f"{sub_category}工程师",
            "开发/后端": f"{sub_category}后端开发",
            "开发/前端": f"{sub_category}前端开发",
            "数据": f"{sub_category}工程师",
            "测试": f"{sub_category}工程师",
            "运维/DevOps": f"{sub_category}工程师",
        }
        job_title = title_map.get(category, f"{sub_category}工程师")

        salary = generate_salary(category)
        skills = generate_skills(category, sub_category)

        welfare_options = ["五险一金", "年终奖", "弹性工作", "餐补", "带薪年假", "股票期权", "远程办公", "培训机会", "团建活动", "补充医疗"]
        welfare = "、".join(random.sample(welfare_options, random.randint(2, 5)))

        month = random.randint(1, 12)
        create_time = f"2026-{month:02d}"

        jobs.append({
            "category": category,
            "sub_category": sub_category,
            "job_title": job_title,
            "province": province,
            "job_location": city,
            "job_company": company,
            "job_industry": industry,
            "job_finance": finance,
            "job_scale": scale,
            "job_welfare": welfare,
            "job_salary_range": salary,
            "job_experience": experience,
            "job_education": education,
            "job_skills": skills,
            "create_time": create_time,
        })
    return jobs


PROJECT_TEMPLATES = [
    {"name": "企业知识库 RAG 问答系统", "level": "核心项目", "skills": "Python,RAG,LangChain,Vector DB,LLM API,FastAPI", "deliverable": "支持上传文档、向量检索、带引用回答、Web API", "why": "覆盖 AI 应用岗位最常见的知识库和检索增强需求"},
    {"name": "数据库 SQL Agent 分析助手", "level": "课程项目", "skills": "Python,SQL,LangChain,LLM API,Visualization", "deliverable": "自然语言提问、生成只读 SQL、结果表格、图表解释", "why": "和数据库课程强相关，展示 agent 不是单纯聊天"},
    {"name": "多工具求职 Agent", "level": "进阶项目", "skills": "Python,LangGraph,LLM API,Git,Evaluation", "deliverable": "岗位解析、技能匹配、项目推荐、面试题生成", "why": "复用原仓库能力，展示工具调用、状态流转和推荐依据"},
    {"name": "LLM 应用评测与日志平台", "level": "工程化项目", "skills": "Python,Evaluation,Monitoring,SQL,Visualization", "deliverable": "保存 prompt、回答、评分、失败案例和趋势图", "why": "补齐 AI 应用工程中经常被忽视的评测和可观测能力"},
    {"name": "AI 应用部署模板", "level": "工程化项目", "skills": "FastAPI,Docker,Redis,Git,Monitoring", "deliverable": "FastAPI 服务、Dockerfile、缓存、日志和健康检查", "why": "把 demo 变成可部署服务，面试时更像真实工程"},
]

LEARNING_RESOURCES = [
    {"skill": "RAG", "title": "RAG 原理到企业知识库实战", "type": "项目文档", "focus": "检索、重排、引用、幻觉控制"},
    {"skill": "LangChain", "title": "LangChain SQL Agent 与 Tool Calling", "type": "框架练习", "focus": "工具调用、SQLDatabase、只读查询约束"},
    {"skill": "FastAPI", "title": "FastAPI 服务化最小模板", "type": "工程模板", "focus": "接口、参数校验、日志、健康检查"},
    {"skill": "Docker", "title": "AI 应用 Docker 部署清单", "type": "部署清单", "focus": "镜像、环境变量、启动脚本、端口"},
    {"skill": "Evaluation", "title": "LLM 应用评测用例库", "type": "面试准备", "focus": "准确率、失败案例、回归测试、日志分析"},
    {"skill": "SQL", "title": "岗位市场分析 SQL 题", "type": "课程练习", "focus": "分组统计、关联查询、共现分析、视图"},
]

SKILL_TRENDS = [
    {"skill": "RAG", "trend_score": 95, "signal": "上升"},
    {"skill": "LLM API", "trend_score": 91, "signal": "上升"},
    {"skill": "Vector DB", "trend_score": 88, "signal": "上升"},
    {"skill": "LangChain", "trend_score": 84, "signal": "上升"},
    {"skill": "Evaluation", "trend_score": 79, "signal": "上升"},
    {"skill": "Docker", "trend_score": 66, "signal": "稳定"},
    {"skill": "SQL", "trend_score": 62, "signal": "稳定"},
    {"skill": "Redis", "trend_score": 56, "signal": "稳定"},
    {"skill": "Python", "trend_score": 85, "signal": "上升"},
    {"skill": "FastAPI", "trend_score": 72, "signal": "上升"},
    {"skill": "Kubernetes", "trend_score": 58, "signal": "稳定"},
    {"skill": "Git", "trend_score": 50, "signal": "稳定"},
]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS raw_jobs (
    job_id INTEGER PRIMARY KEY,
    category TEXT,
    sub_category TEXT,
    job_title TEXT,
    province TEXT,
    job_location TEXT,
    job_company TEXT,
    job_industry TEXT,
    job_finance TEXT,
    job_scale TEXT,
    job_welfare TEXT,
    job_salary_range TEXT,
    job_experience TEXT,
    job_education TEXT,
    job_skills TEXT,
    create_time TEXT,
    salary_floor_k REAL
);

CREATE TABLE IF NOT EXISTS job_skill_map (
    job_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES raw_jobs(job_id)
);

CREATE TABLE IF NOT EXISTS project_templates (
    project_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    level TEXT,
    deliverable TEXT,
    why TEXT
);

CREATE TABLE IF NOT EXISTS project_skill_map (
    project_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES project_templates(project_id)
);

CREATE TABLE IF NOT EXISTS learning_resources (
    resource_id INTEGER PRIMARY KEY,
    skill TEXT NOT NULL,
    title TEXT NOT NULL,
    type TEXT,
    focus TEXT
);

CREATE TABLE IF NOT EXISTS skill_trends (
    skill TEXT PRIMARY KEY,
    trend_score INTEGER NOT NULL,
    signal TEXT,
    source TEXT
);

CREATE INDEX IF NOT EXISTS idx_raw_jobs_category ON raw_jobs(category);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_province ON raw_jobs(province);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_industry ON raw_jobs(job_industry);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_finance ON raw_jobs(job_finance);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_experience ON raw_jobs(job_experience);
CREATE INDEX IF NOT EXISTS idx_job_skill_skill ON job_skill_map(skill);
CREATE INDEX IF NOT EXISTS idx_job_skill_job ON job_skill_map(job_id);
"""


def build_database():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    jobs = generate_jobs(200)

    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA_SQL)

    for job_id, job in enumerate(jobs, 1):
        salary_floor = random_salary_floor(job["job_salary_range"])
        conn.execute("""
            INSERT INTO raw_jobs (job_id, category, sub_category, job_title, province, job_location,
                job_company, job_industry, job_finance, job_scale, job_welfare,
                job_salary_range, job_experience, job_education, job_skills, create_time, salary_floor_k)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (job_id, job["category"], job["sub_category"], job["job_title"],
              job["province"], job["job_location"], job["job_company"], job["job_industry"],
              job["job_finance"], job["job_scale"], job["job_welfare"], job["job_salary_range"],
              job["job_experience"], job["job_education"], job["job_skills"], job["create_time"],
              salary_floor))

        skills = [s.strip() for s in job["job_skills"].split(",") if s.strip()]
        for skill in skills:
            conn.execute("INSERT INTO job_skill_map (job_id, skill) VALUES (?, ?)", (job_id, skill))

    for i, proj in enumerate(PROJECT_TEMPLATES, 1):
        conn.execute("INSERT INTO project_templates (project_id, name, level, deliverable, why) VALUES (?, ?, ?, ?, ?)",
                     (i, proj["name"], proj["level"], proj["deliverable"], proj["why"]))
        for skill in proj["skills"].split(","):
            conn.execute("INSERT INTO project_skill_map (project_id, skill) VALUES (?, ?)", (i, skill.strip()))

    for i, res in enumerate(LEARNING_RESOURCES, 1):
        conn.execute("INSERT INTO learning_resources (resource_id, skill, title, type, focus) VALUES (?, ?, ?, ?, ?)",
                     (i, res["skill"], res["title"], res["type"], res["focus"]))

    for trend in SKILL_TRENDS:
        conn.execute("INSERT INTO skill_trends (skill, trend_score, signal, source) VALUES (?, ?, ?, ?)",
                     (trend["skill"], trend["trend_score"], trend["signal"], "Job-市场调研"))

    conn.commit()
    conn.close()
    print(f"Database created: {DB_PATH}")
    print(f"Jobs: {len(jobs)}")
    print(f"Tables: raw_jobs, job_skill_map, project_templates, project_skill_map, learning_resources, skill_trends")


if __name__ == "__main__":
    build_database()
