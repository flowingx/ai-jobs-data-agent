# 用户 taste / 项目偏好功能说明草案

> 这是给 README / SKILL 文档使用的功能说明草案。正式实现后，可以把其中的“推荐用法”“CLI 示例”“候选 JSON 示例”同步到主文档。
>
> 当前落地状态：`SKILL.md` 已写入 JD 后 yes/no taste gate 和 A/B/C/D 流程；`candidate_score.py` 已支持 `--taste`、`raw_score`、`max_raw_score`、`score_breakdown.user_preference` 和小数排序；`README.md` / `README.en.md` 已同步正式用法。因此下面的 CLI `--taste` 示例是可运行接口。

## 功能一句话

在输入 JD 后，工具会先询问用户是否有自己的项目偏好（taste）。如果用户选择“没有”，继续原 workflow；如果选择“有”，工具会提供 A/B/C/D 四个选项，其中 A/B/C 由模型根据 JD 项目大概分类自动生成，并在用户已提供个人信息时一并考虑；D 是直接可填写的自定义输入框。最终选定的 taste 会作为额外评分维度，帮助推荐更适合用户的项目。

## 什么时候使用

适合这些场景：

- 同一个 JD 能匹配多个项目方向，需要按用户偏好进一步筛选。
- 用户想把项目做得更像“自己的项目”，而不是只追 JD 关键词。
- 用户有明确避雷项，比如不想碰纯前端、多机多卡、复杂云账号、过重环境。
- 用户需要更适合面试讲的项目，而不是只追求技术名词堆叠。

## 推荐用法

推荐先把目标 JD 和个人情况发给 AI 助手；工具会在 JD 初步分析后询问是否有 taste。如果你已经有明确偏好，也可以在初始输入里直接写出来，但这不会跳过 yes/no gate；工具会先确认是否将这段内容作为 D 自定义偏好：

```text
使用鼠鼠实习妙妙工具，根据下面这份 JD 帮我规划一个能投递、能面试、能讲清的计算机实习项目。

我的情况：
- 当前水平：学过课程但项目少
- 熟悉语言/框架：Python、FastAPI、一点 React
- 时间预算：2 天
- 本地/远程资源：本地电脑 + Docker，无 GPU
- 希望运行深度：smoke-test
- 项目偏好 / taste：更想做后端 + AI 应用；希望能本地跑通，适合面试讲；不想做纯前端，不想依赖多机多卡或复杂云服务。

JD：
...
```

如果暂时没有偏好，可以写：

```text
项目偏好 / taste：无，按 JD 推荐。
```

或者只给 JD，让工具在 JD 初步分析后先问你是否有项目偏好；如果你选择“有”，工具会给出 A/B/C/D 四个选项，其中 A/B/C 由模型自动生成，D 是你直接填写的输入框。

## Agent 应该怎么问

用户发送 JD 后，agent 先完成 JD 初步理解和项目大概分类，然后只问一次 yes/no：用户是否有自己的项目偏好 / taste。

第一步：先问是否有偏好。

```text
我已经看完这份 JD。你对要做的项目有没有自己的偏好 / taste？
比如更想做 AI、后端、数据、基础架构、前端，或者希望项目更容易本地跑通、更适合面试讲、更有技术深度。

请选择：
1. 有，我想选择或输入自己的项目偏好。
2. 没有，按 JD 和默认稳妥策略推荐。
```

如果用户选择“没有”，就继续原 workflow，不再追问 taste，也不加 taste 权重。

如果用户选择“有”，再给出 A/B/C/D 四个选项。A/B/C 是模型根据 JD 项目大概分类自动分析出来的推荐偏好；如果用户已提供个人信息、技术栈、时间预算或资源条件，就同时考虑；没有提供时只按 JD 和保守默认生成。D 是用户自己直接填写的输入框：

```text
基于这份 JD，以及你已提供的个人信息（如有），我给你 4 个项目偏好选项：

A. 后端工程落地型：偏 API / 数据库 / 鉴权 / 缓存，目标是本地 Docker 能跑通，适合面试讲工程链路。
B. AI 应用增强型：偏 RAG / LLM 应用 / 评估 / serving，目标是在不依赖重 GPU 的情况下做出可演示 AI 功能。
C. 稳妥面试型：偏低环境风险、2 天内 smoke test、简历和面试表达清晰，技术深度适中。
D. __________________（我自己输入：请直接在这里写“我更想做 XXX，不想做 XXX，希望项目 XXX”）
```

上面的 A/B/C 只是格式示例，实际实现时应由模型根据 JD 对应的项目大概分类动态生成；用户给了个人信息就一起考虑，没给就不依赖个人信息。

如果用户在初始消息里已经写了 taste，仍然必须先问 yes/no 确认：选择“是”才作为 D 自定义偏好，选择“否”就忽略这段偏好并按 JD 默认策略推荐。

交互 gate 是显式 yes/no 选择，不解析自由文本；用户只有选择“有”之后，才会进入 A/B/C/D，其中 D 是自定义输入框 / 填空项。

如果用户在 D 自定义输入里写了“不要 / 不想 / 避免 / 不希望”，agent 应把这些内容视为避雷项，而不是正向偏好。例如“我不想做纯前端”应归为避雷 `pure-frontend`，不能给纯前端项目加分。

## README 同步建议

README 里需要把旧的“技术栈偏好 / 最多 5 问”口径更新为下面这条主流程：

```text
用户发送 JD 后，工具会先问：你是否有自己的项目偏好 / taste？
- 选择“没有”：按原 workflow 根据 JD、技能匹配、可运行性和项目风险推荐。
- 选择“有”：工具展示 A/B/C/D 四个选项。
  - A/B/C：模型根据 JD 项目大概分类自动生成；如果用户给了个人信息，则同时考虑。
  - D：直接可填写的自定义输入框，例如“D. ________”。
- 如果初始消息里已经写了 taste，也仍然先问 yes/no：是否把它作为 D 自定义偏好。
```

README 的 CLI 部分已可把 `candidate_score.py --taste taste.txt` 作为正式命令发布。

## CLI 示例

无 taste，保持旧用法：

```bash
python -m shushu_internship_tool.candidate_score \
  --jd jd.txt \
  --candidates candidates.json \
  --out reports/ranking
```

有效 taste，增加可选参数：

```bash
python -m shushu_internship_tool.candidate_score \
  --jd jd.txt \
  --candidates candidates.json \
  --taste taste.txt \
  --out reports/ranking
```

`taste.txt` 示例：

```text
更想做后端 + AI 应用；希望 Docker 本地跑通；适合面试讲；不想做纯前端；不要多机多卡。
```

## 候选 JSON 示例

```json
[
  {
    "name": "tiny-ai-backend",
    "repo_url": "https://github.com/example/tiny-ai-backend",
    "license": "MIT",
    "stars": 350,
    "last_commit": "2026-05-01",
    "tags": ["fastapi", "postgresql", "rag", "docker"],
    "jd_keywords": ["api", "database", "docker"],
    "matched_jd_terms": ["后端", "API", "Docker"],
    "runnable": true,
    "compute": "local_docker",
    "mod_ideas": ["add JWT auth", "add Redis cache", "add RAG evaluation"],
    "risk_notes": ["vector database config needs verification"],
    "taste_tags": ["backend", "ai-app", "local-docker", "interview-friendly"],
    "project_taste_notes": [
      "偏后端 + AI 应用形态",
      "Docker Compose 可本地 smoke test",
      "API / 数据库 / 检索链路适合面试讲"
    ],
    "avoid_tags": ["cloud-heavy"]
  }
]
```

字段含义：

- `taste_tags`：项目自身可匹配的偏好标签，例如后端、AI 应用、本地 Docker、适合面试讲。
- `project_taste_notes`：候选项目的通用 taste 说明，不绑定某个具体用户，不建议用于脚本打分。
- `user_preference_notes`：输出结果里针对当前用户 taste 生成的匹配解释，不是候选 JSON 的静态输入字段。
- `avoid_tags`：项目自身可能让部分用户避雷的属性，例如纯前端、多机多卡、云依赖重、大数据集；真正命中用户避雷项后，应在输出里展示为 `taste_mismatches`。

## 输出应该体现什么

推荐项目时，除了原来的 JD 匹配、可运行性、资源成本、魔改空间和风险，还应补充：

- 用户 taste 匹配点。
- 不匹配或有风险的偏好点。
- 为什么这个项目比另一个项目更适合该用户。
- 如果用户没有 taste，则按 JD 和默认保守策略推荐，不额外加 taste 权重。

示例：

```text
主项目推荐：tiny-ai-backend
- JD 匹配：命中 FastAPI、PostgreSQL、Docker、API design。
- 用户 taste 匹配：后端 + AI 应用，本地 Docker 可 smoke test，有 API / DB / 检索链路，适合面试讲。
- 不符合 taste 的点：如果真实向量数据库配置复杂，可以先 mock，避免第一天卡环境。
- 风险：向量数据库配置需要确认，建议第一天先用 mock 数据跑通。
- 结论：适合作为主项目；2 天内目标是 smoke test + 一个可讲的鉴权或缓存改造。
```

## 分数说明

脚本可以先计算 raw score，再把 raw score clamp 到对应区间，最后映射到 0-100 分，最终 `score` 保留两位小数：

```python
x = max(0, min(raw_score, max_raw_score))
score = round(x * 100 / max_raw_score, 2)
```

- 无 taste：原有正向满分是 104，`max_raw_score = 104`，使用 `score = round(x * 100 / 104, 2)`。
- 有效 taste：新增 `user_preference` 后正向满分是 114，`max_raw_score = 114`，使用 `score = round(x * 100 / 114, 2)`。
- `--taste` 未传、文件为空、只有空白，或内容仅等价于“无 / 都可以 / 跳过 / none / no preference”且没有具体偏好时，都按无有效 taste 处理，分母仍然是 104；如果文本包含具体偏好，例如“无，但更偏后端”，则按有效 taste 处理。

这样负 raw score 会先归零，无有效 taste 满分 104 和有效 taste 满分 114 都能分别映射为 100.00。不要直接使用 `raw_score * 100 / max_raw_score`，否则 raw score 为负时会输出负分。

## 注意事项

- taste 是加分项，不是硬性替代 JD 匹配。
- 如果项目不可运行、资源过重、风险过高，即使符合 taste，也不应该轻易推荐为主项目。
- 如果用户在交互 gate 里选择“没有”，或 `--taste` 文件为空，就不做额外 taste 加权，并按无有效 taste 分母 104 计分。`--taste` 文本文件中如果同时包含具体偏好，则按有效 taste 处理。
- 第一版只做显式匹配、简单中英文 alias 和 agent 解释，不追求复杂 NLP。
- 现有英文 tokenizer 不能完整处理“后端”“本地跑通”“不想做纯前端”等中文表达，需要 substring matching、alias 表，或由 agent 预先归一化。
- `SKILL.md` 中已删除“如果当前 `candidate_score` 尚未支持 `--taste`”的过渡说明，README / Skill 保持同一条主路径。
