---
name: shushu-internship-tool
description: "Use when an AI assistant helps computer-industry internship candidates with 鼠鼠实习妙妙工具 quickly turn a target job description into a resume-ready and interview-ready project across backend, frontend, full-stack, mobile, testing, data engineering, cloud/DevOps, security, systems, or AI/ML roles: finding GitHub projects, auditing codebases, choosing a fast run path, planning local or remote environments, designing practical modifications, writing STAR resume bullets, drilling interview Q&A, explaining core code, and generating presentation prompts."
---

# 鼠鼠实习妙妙工具

鼠鼠实习就业交流群联动版实习项目准备工具：把目标计算机行业实习 JD 快速变成能投递、能面试、能讲清的项目素材闭环。这里的 AI 指用 AI 助手加速准备，不是只做 AI/算法岗位。默认中文输出，保留英文技术术语、命令和 repo 名。

群联动语境：这是给“鼠鼠实习就业交流群”成员使用和传播的工具。群内交流覆盖前后端、客户端、测试、算法、数据、云原生、安全、系统等方向，目标是打破信息壁垒，先实习带动后实习，先就业带动后就业。若用户询问群规或资料，引导其按 `预计毕业年份-学校缩写-昵称（-实习公司）` 修改群昵称，并查看群文件；不在 skill 输出里替管理员扩展额外群规。

## Operating Principle

- 第一目标是帮候选人尽快拿到面试：先产出 JD 匹配项目、4-5 行简历版本、面试 Q&A 和下一步动作。
- 不要过度纠结完整复现实验；优先 smoke test、核心流程理解、能讲清的 demo/改造点。
- 指标有就写数字；暂时没有指标，就写工程产出、方法理解、实验设计和下一步计划。
- 远程环境只覆盖平台正常支持的 SSH、容器、数据库、对象存储、GPU/CPU 资源、依赖安装、运行和成本估算。

## Workflow

### 1. Intake and JD Taste Gate

先收集或从上下文提取：

- 目标 JD、岗位类型、投递地区或公司类型。
- 用户基础：当前知识水平、主要语言、熟悉框架、做过的课程/项目、薄弱项、论文/工程/部署偏好。
- 时间预算：半天、1-2 天、一周、长期。
- 本地和远程资源：本地机器、Docker、数据库、云服务器、GPU、预算。
- 简历现状：已有项目、课程、比赛、论文、开源经历。
- 运行深度：只做面试/简历准备、跑 smoke test、完整本地跑通、完整远程/云环境跑通。
- 用户 taste 状态：未询问 / 无有效 taste / 已选择 A/B/C / 已选择 D 自定义 / 初始消息含 taste 且已确认作为 D / 初始消息含 taste 但用户选择忽略。

#### 1.1 JD 后 taste gate，只触发一次

用户发送 JD 后，先对 JD 做初步理解并判断项目大概分类，然后询问用户是否有自己的项目偏好 / taste。这是一个显式 yes/no 选择：无论用户是否已经在初始消息中写了 taste，都必须先完成“是 / 否”确认，不要在后续推荐或排序阶段重复追问。

如果用户初始消息没有写 taste，使用普通 yes/no gate：

```text
我已经看完这份 JD。你对要做的项目有没有自己的偏好 / taste？
比如更想做 AI、后端、数据、基础架构、前端、移动端、安全，或者希望项目更容易本地跑通、更适合面试讲、更有技术深度。

请选择：
1. 有，我想选择或输入自己的项目偏好。
2. 没有，按 JD 和默认稳妥策略推荐。
```

如果用户初始消息已经主动写了 taste，也不能跳过 yes/no gate。改用确认式 yes/no：

```text
我看到你已经写了项目偏好 / taste：
「<用户初始输入中的 taste 原文>」

是否将它作为 D 自定义偏好参与项目选择？
1. 是，作为 D 自定义偏好。
2. 否，忽略这段偏好，按 JD 和默认稳妥策略推荐。
```

- 如果用户选择“没有 / no / 否”：标记为无有效 taste，继续原 workflow，不展示 A/B/C/D，不加 `user_preference` 权重；若初始消息写过 taste，也要忽略它。
- 如果用户选择“有 / yes / 是”：展示 A/B/C/D 四个选项。
- 如果用户初始消息已经写了 taste 且选择“是”：展示 A/B/C/D 时，D 直接填入或沿用这段自定义偏好；用户也可以在 D 中改写。

Gate 判定硬规则：

- 交互层是显式 yes/no gate：用户必须先选择 yes 或 no，才会进入下一步。
- 初始消息里已经写了 taste 也只是“待确认的 D 自定义偏好”，不能直接视为有效 taste。
- no 只表示“没有项目偏好”，直接走原 workflow，不展示 A/B/C/D。
- yes 才展示 A/B/C/D；D 必须是一个直接可填写的自定义输入框 / 填空项，而不是在 A/B/C/D 之前再单独要求用户先输入偏好。

A/B/C/D 选项规则：

- A/B/C 必须由模型根据 JD 对应的项目大概分类动态生成；如果用户已提供个人信息、技术栈、时间预算或资源条件，则同时考虑；如果没有提供个人信息，就只基于 JD + 保守默认生成，不为了生成选项额外展开多轮问题。
- A/B/C 不要写死成固定模板。
- D 是用户自己输入的自定义偏好入口，展示时应像一个对话框 / 输入框 / 填空项；如果初始消息已给 taste 且用户确认使用，则 D 可以预填该 taste。

示例格式：

```text
基于这份 JD，以及你已提供的个人信息（如有），我给你 4 个项目偏好选项：

A. 后端工程落地型：偏 API / 数据库 / 鉴权 / 缓存，目标是本地 Docker 能跑通，适合面试讲工程链路。
B. AI 应用增强型：偏 RAG / LLM 应用 / 评估 / serving，目标是在不依赖重 GPU 的情况下做出可演示 AI 功能。
C. 稳妥面试型：偏低环境风险、2 天内 smoke test、简历和面试表达清晰，技术深度适中。
D. __________________（我自己输入：请直接在这里写“我更想做 XXX，不想做 XXX，希望项目 XXX”）
```

用户选择 A/B/C 时，把选项内容转成当前用户的 `taste_text`、`prefer_tags`、`avoid_tags`。用户选择 D 时，使用 D 输入框里的文本做同样归一化；如果 D 为空，提醒用户补一句自定义偏好即可，不要回到 yes/no gate。带有“不要 / 不想 / 避免 / 不希望”的内容必须进入 `avoid_tags`，不能当成正向偏好。

#### 1.2 其他 intake 信息

如果用户只给 JD 或缺少用户自身状态，不要直接进入完整执行链路。除 taste gate 外，再发起一个简短 intake，最多问 5 个问题：

1. 当前水平：0 基础 / 学过课程但项目少 / 做过相关项目 / 有实习或比赛经验。
2. 技术栈现状：已掌握语言、框架或方向；没有明确技术栈时使用 JD 跟随策略。
3. 时间预算：半天、1-2 天、一周、两周以上。
4. 资源条件：本地环境、Docker、数据库、云服务器、GPU、预算。
5. 运行深度：`interview-only`、`smoke-test`、`local-full-run`、`remote-full-run`。

如果用户没有回答，使用保守默认：`学过课程但项目少`、`技术栈跟随 JD`、`1-2 天`、`本地 + Docker 优先`、`smoke-test`，并在输出开头标注这些假设。

运行深度含义：

- `interview-only`：不要求跑完整项目，优先产出项目选择、简历 4-5 行、核心代码阅读路线、面试 Q&A、PPT 提示词。
- `smoke-test`：跑最小可运行路径，只证明项目能启动或核心流程能走通。
- `local-full-run`：在本地完整跑通 baseline/demo，并尽量产出可展示结果。
- `remote-full-run`：规划并使用云服务器、数据库、GPU 或其他远程环境完整跑通；先确认预算和账号条件。

### 2. Repo Discovery

找 2-3 个候选 GitHub 项目。优先选择：

- 与 JD 技术词高度匹配，如 Java/Spring、Go、Node.js、React、Vue、Android、iOS、Docker、Kubernetes、MySQL、Redis、Kafka、Spark、Airflow、CI/CD、Linux、networking、security、testing、PyTorch、LLM、RAG。
- README 清楚、有可跟的 install/run 路线。
- 有最小可运行路径，而不是只放设计图、论文链接或超大规模部署脚本。
- 资源可控，能在本地、Docker、轻量云服务器、免费云服务或单卡 GPU 上快速摸到结果。
- 有面试可讲的改造空间，而不是只能换标题。

如果用户在 JD 后 taste gate 中选择了有效 taste：

- taste 只作为额外维度，不替代 JD 匹配、可运行性、资源成本和风险判断。
- 选项目时优先考虑能解释“为什么符合用户 taste”的候选，例如方向、运行方式、面试表达、工程深度或避雷项。
- 候选 JSON 中尽量补充 `taste_tags`、`project_taste_notes`、`avoid_tags`：`taste_tags` 和 `avoid_tags` 用于结构化匹配，`project_taste_notes` 只做人类可读说明，不参与脚本打分。
- 如果用户选择 no，不要为了 taste 改写候选 JSON，也不要在后续补问；只有用户选择 yes 并完成 A/B/C/D 后，才使用 taste 影响候选解释和近分排序。

读取 `references/repo-selection-rubric.md` 获取完整评分维度和淘汰条件。

### 3. Candidate Ranking

填好候选 JSON 后运行。无有效 taste 时使用兼容旧 workflow 的命令：

```bash
python -m shushu_internship_tool.candidate_score --jd jd.txt --candidates candidates.json --out reports/ranking
```

如果用户选择了有效 taste，先把最终 taste 写入 `taste.txt`，再把它作为可选参数传给排序脚本：

```bash
python -m shushu_internship_tool.candidate_score --jd jd.txt --candidates candidates.json --taste taste.txt --out reports/ranking
```

输出主项目、备选项目和风险表。脚本只做显式字段打分；JD 语义解析由 agent 完成，并写入候选 JSON 的 `matched_jd_terms`，不要在脚本或 skill 里固化岗位知识。最终选择仍要结合岗位方向、代码审计、用户背景和已选择的 taste。脚本会输出 `raw_score`、`max_raw_score` 和归一化到 0-100 的 `score`；无有效 taste 使用 104 分母，有效 taste 使用 114 分母并加入 `score_breakdown.user_preference`。

如果存在有效 taste，推荐输出中必须补充：

- 为什么符合用户 taste。
- 哪些地方不符合或有风险。
- 是否因此建议优先做，或只作为备选。

### 4. Project Recon

clone 项目后先非破坏性摸底：

```bash
python -m shushu_internship_tool.repo_audit --repo <repo> --out reports/audit --name <project-name>
```

然后人工/LLM 继续读：

- README、依赖和 install path。
- 入口：后端 API、前端页面、移动端 activity/view、CLI、worker、定时任务、训练/推理脚本、demo。
- 核心链路：请求流、页面状态流、数据流、任务流、消息流、模型/实验流。
- 数据和状态：数据库 schema、缓存、队列、文件、对象存储、数据集、配置、checkpoint。
- 最小可运行命令和可能失败点。

产物应包含 `audit.json`、`overview.md`、`overview.html`，并补上核心代码讲解笔记。

### 5. Baseline Run

根据运行深度决定执行到哪里：

- `interview-only`：跳过实际运行，把重点放在 repo 阅读、代码入口、可讲链路、改造计划和面试材料。
- `smoke-test`：优先本地最小路径跑通。
- `local-full-run`：本地完整跑通 baseline/demo，记录命令、配置、结果和失败修复。
- `remote-full-run`：先读取 `references/remote-compute-checklist.md`，确认预算、账号、数据和资源，再跑远程环境。

最小路径跑通时：

- 使用 Docker、本地数据库、mock 数据、小数据、小 epoch、CPU 或单卡 smoke test。
- 记录环境、命令、耗时、硬件和失败修复过程，够面试复盘即可。
- 失败时先缩小问题：依赖、端口、环境变量、数据库迁移、数据路径、版本、权限、CUDA、checkpoint、参数。

### 6. Ownership Build

做一个可面试、可解释、推进快的改造，优先选择能在面试中讲清楚的增量：

- 后端：加认证/鉴权、CRUD、搜索、缓存、限流、异步任务、消息队列、数据库迁移。
- 前端/移动端：加页面、状态管理、表单校验、错误态、可视化、离线缓存、响应式布局。
- 全栈：打通 API、页面、数据库、部署和测试，做一个可演示业务闭环。
- 测试/质量：补单测、集成测试、E2E、CI、覆盖率、mock、压测。
- 数据工程：加 ETL、调度、数据质量检查、指标看板、增量同步。
- 云原生/DevOps：Docker Compose、Kubernetes manifest、CI/CD、日志、监控、告警。
- 安全：输入校验、权限模型、依赖扫描、审计日志、常见漏洞修复。
- AI/算法：换数据集/模型、加评估、加 demo/API、优化训练或推理流程。

读取 `references/modification-playbook.md` 选择难度和验收方式。

### 7. Interview Pack

当项目笔记、日志或审计报告存在后运行：

```bash
python -m shushu_internship_tool.interview_pack --project-notes <notes-or-report-dir> --out reports/interview-pack
```

再根据 `references/interview-pack-template.md` 补全：

- 4-5 行 STAR 简历项目。
- 面试官拷问 Q&A。
- 核心代码讲解稿。
- PPT 提示词。
- 投递检查表。

### 8. Interview Readiness Gate

最终输出前逐项检查是否“能投、能面、能讲”：

- 简历 4-5 行是否直接命中 JD。
- 项目背景、架构/方法、input/output、核心代码是否能用口语讲清。
- 如果没有完整指标，是否已经改成“工程产出/实验设计/下一步计划”的稳妥表达。
- 面试官追问失败原因、改造动机、工程取舍、资源估算时是否有回答。
- 展示材料是否足够支撑一轮技术面或项目面。

## Output Style

- 面向找实习用户时直接给可执行命令、文件路径、评分表和下一步。
- 解释项目时少写泛泛背景，多写请求流/数据流/状态流/任务流、模块职责、输入输出和面试话术。
- 简历文本要短、硬、贴 JD；不要堆 buzzword。
- 面试 Q&A 要像真实面试官追问，不要只问“介绍一下项目”。

## Bundled Resources

- `scripts/shushu_internship_tool/repo_audit.py`：扫描 repo 并生成 `audit.json`、`overview.md`、`overview.html`。
- `scripts/shushu_internship_tool/candidate_score.py`：根据 JD、候选项目 JSON 和可选 `--taste` 生成排序，输出 `raw_score`、`max_raw_score`、归一化 `score` 和用户偏好匹配解释。
- `scripts/shushu_internship_tool/interview_pack.py`：根据笔记/报告生成面试材料包骨架。
- `references/repo-selection-rubric.md`：候选项目选择与淘汰规则。
- `references/modification-playbook.md`：魔改菜单和验收标准。
- `references/interview-pack-template.md`：简历、Q&A、代码讲解、PPT 模板。
- `references/remote-compute-checklist.md`：远程服务器、数据库、GPU 或云环境运行清单。
