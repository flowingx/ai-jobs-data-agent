# 用户 taste / 项目偏好功能设计

## 1. 背景

当前 SIT 的核心链路是：

```text
JD → intake → repo discovery → candidate ranking → repo audit → baseline run → ownership build → interview pack
```

现有 intake 已经收集用户水平、技术栈、时间预算、资源条件和运行深度，但“用户自己的项目 taste”表达不够独立。实际选项目时，同一个 JD 可能对应多个合理项目：

- 有人更想做后端工程项目。
- 有人更想做 AI / RAG / 推荐方向。
- 有人希望项目本地能跑通。
- 有人希望项目更适合面试讲，而不是追求炫技。
- 有人不想碰前端、不想碰 GPU、不想碰复杂云资源。

因此需要增加一个可选维度：用户 taste / 项目偏好。

## 2. 目标

### 2.1 产品目标

- 在用户发送 JD 后，先用 yes/no 询问是否有项目偏好；选择“否”时走原 workflow，选择“是”时展示 A/B/C/D 四个偏好选项，其中 D 是直接可填写的自定义输入框。
- 推荐项目时体现“JD 匹配 + 用户 taste 匹配”。
- 用户不填 taste 时不打断旧 workflow。
- 帮助 agent 更早排除“不适合这个用户”的项目。

### 2.2 工程目标

- 在 skill prompt、rubric、README 和 candidate_score 中保持同一套概念。
- `candidate_score` 支持一个可选 taste 输入，输出可解释分数。
- 保持向后兼容：旧 candidates JSON 和旧 CLI 命令仍可运行；未传 taste 时不引入 taste 排序因素。
- 分数采用 raw score → 0-100 的归一化映射，避免新增 taste 后总分上限变化导致分数含义不一致。

### 2.3 非目标

- 不做复杂推荐系统。
- 不用网络 API 或外部模型做语义匹配。
- 不让 taste 覆盖硬性淘汰条件。
- 不在脚本内硬编码完整岗位族语义；语义分析仍主要交给 agent。

### 2.4 当前实现状态

截至本文档当前版本，首版 taste 功能已接入主路径：

- `candidate_score.py` 已支持 `--taste`、`taste_score()`、`normalize_score()`、`raw_score`、`max_raw_score`、`score_breakdown.user_preference`、`safe_float()` 和小数排序。
- `README.md` / `README.en.md` 已同步 JD 后 yes/no taste gate、A/B/C/D 流程、`--taste` CLI 示例和分数归一化说明。
- `SKILL.md` 已删除开发期“如果 `candidate_score` 暂不支持 `--taste`”过渡说明，排序阶段按无 taste / 有 taste 两条正式命令走。
- `docs/` 当前属于新增文档目录，提交前需要确认已加入版本控制。

## 3. 用户体验设计

### 3.1 JD 后的 taste 选择流程

用户发送 JD 后，agent 先完成 JD 初步理解和项目大概分类，然后只触发一次 taste 选择。流程不是“在 intake 问一次、后面再问一次”，而是固定为下面这个二段式选择，并且无论用户是否在初始消息里写过 taste，都必须先经过 yes/no gate：

```text
1. agent 问用户是否有自己的项目偏好 / taste：
   - 否：标记为无有效 taste，继续原 workflow，不展示 A/B/C/D，不加 user_preference 分。
   - 是：进入第 2 步。

2. agent 展示 A/B/C/D 四个选项：
   - A/B/C：由模型根据 JD 对应的项目大概分类自动生成；如果用户已提供个人信息、技术栈、时间预算或资源条件，则同时考虑；没提供时只基于 JD 和保守默认生成。
   - D：用户自己输入项目偏好，展示形式必须是直接可填写的输入框 / 填空项。
```

第一步 yes/no 问法示例：

```text
我已经看完这份 JD。你对要做的项目有没有自己的偏好 / taste？
比如更想做 AI、后端、数据、基础架构、前端，或者希望项目更容易本地跑通、更适合面试讲、更有技术深度。

请选择：
1. 有，我想选择或输入自己的项目偏好。
2. 没有，按 JD 和默认稳妥策略推荐。
```

如果用户初始消息里已经主动写了 taste，不直接视为有效 taste，而是先做确认式 yes/no：

```text
我看到你已经写了项目偏好 / taste：
「<用户初始输入中的 taste 原文>」

是否将它作为 D 自定义偏好参与项目选择？
1. 是，作为 D 自定义偏好。
2. 否，忽略这段偏好，按 JD 和默认稳妥策略推荐。
```

如果用户选择“没有 / 否”，立刻回到旧 workflow，不再追问 taste；如果初始消息里写过 taste，也忽略这段偏好。

如果用户选择“有 / 是”，agent 再展示四个选项。A/B/C 必须是动态生成项，不是固定模板；生成依据以 JD 分析出的项目大概分类为主，若用户已经提供个人信息、技术栈、时间预算或资源条件，则一并考虑：

```text
基于这份 JD，以及你已提供的个人信息（如有），我给你 4 个项目偏好选项：

A. 后端工程落地型：偏 API / 数据库 / 鉴权 / 缓存，目标是本地 Docker 能跑通，适合面试讲工程链路。
B. AI 应用增强型：偏 RAG / LLM 应用 / 评估 / serving，目标是在不依赖重 GPU 的情况下做出可演示 AI 功能。
C. 稳妥面试型：偏低环境风险、2 天内 smoke test、简历和面试表达清晰，技术深度适中。
D. __________________（我自己输入：请直接在这里写“我更想做 XXX，不想做 XXX，希望项目 XXX”）
```

如果用户初始消息已给 taste 且确认使用，则 D 可以预填或沿用该文本；用户也可以在 D 中改写。用户选择 A/B/C 时，agent 将该选项内容转成当前用户的 `taste_text`、`prefer_tags` 和 `avoid_tags`；用户选择 D 时，agent 使用 D 输入框里的文本作为 `taste_text` 并做同样归一化。

约束：

- taste 选择只触发一次；选择“没有 / no / 否”后，不在后续推荐 / 排序阶段再次追问。
- 初始消息里已经主动写了 taste 也必须先确认：选择“是”才作为 D 自定义偏好；选择“否”则忽略。
- 如果用户个人信息不足，A/B/C 可以只基于 JD 大概分类生成保守选项；不要为了生成 A/B/C 再额外展开多轮问题。

交互 gate 的 yes/no 判定规则必须写死：

| 用户操作 | 判定 |
| --- | --- |
| 选择“有 / yes / 是” | yes，展示 A/B/C/D |
| 选择“没有 / no / 否” | no，继续原 workflow，不展示 A/B/C/D |
| 初始消息里已经写了明确 taste，并选择“是，作为 D 自定义偏好” | yes，展示 A/B/C/D，D 预填或沿用该 taste |
| 初始消息里已经写了明确 taste，但选择“否” | no，忽略该 taste，继续原 workflow |

交互 gate 不是自由文本输入；用户只有选择 yes 之后，才会在 D 选项中输入自定义偏好。D 应直接呈现为输入框 / 填空项，而不是在 A/B/C/D 前增加“先输入偏好”的额外步骤。`NOOP_TASTE_TEXTS` 这类兼容词属于 `--taste` 文本文件规则，不属于交互 gate。

### 3.2 用户输入示例

```text
我的 taste：
- 更想做后端 + AI 应用，不想做纯前端。
- 希望能本地 Docker 跑通，不要多机多卡。
- 项目要适合面试讲，有 API、数据库、缓存或队列链路。
- 时间只有 2 天，所以不要太重。
```

agent 需要把这类自然语言拆成两类信息：

```json
{
  "prefer_tags": ["backend", "ai-app", "local-docker", "interview-friendly", "api", "database"],
  "avoid_tags": ["pure-frontend", "multi-gpu", "cloud-heavy", "too-heavy"]
}
```

其中“不要 / 不想 / 避免 / 不希望”等否定表达必须进入 `avoid_tags`，不能被当成正向偏好。

### 3.3 输出示例

```text
主项目推荐：xxx
原因：
- JD 匹配：命中 FastAPI、PostgreSQL、Docker、测试。
- 用户 taste 匹配：后端 + AI 应用，支持 Docker 本地启动，有 API / DB 链路，2 天内可做 smoke test。
- 不符合 taste 的点：向量数据库配置需要确认；如果没有 mock 数据，第一天可能卡环境。
- 风险：README 的向量数据库配置需要确认。
```

## 4. 数据结构设计

### 4.1 新增 taste 输入文件

`taste.txt` 是纯文本，可选：

```text
更想做后端 + AI 应用；希望 Docker 本地跑通；适合面试讲；不想做纯前端；不要多机多卡。
```

CLI：

```bash
python -m shushu_internship_tool.candidate_score \
  --jd jd.txt \
  --candidates candidates.json \
  --taste taste.txt \
  --out reports/ranking
```

`--taste` 的有效性规则必须写死，避免 104 / 114 分母漂移：

| 输入情况 | 计分口径 |
| --- | --- |
| 未传 `--taste` | 按无有效 taste 处理，`has_effective_taste = false`，`max_raw_score = 104` |
| `--taste` 文件为空或只有空白字符 | 按无有效 taste 处理，`max_raw_score = 104` |
| `--taste` 内容只等价于“无 / 都可以 / 跳过 / none / no preference”，且没有任何具体偏好 | 按无有效 taste 处理，`max_raw_score = 104` |
| `--taste` 包含有效偏好或避雷项，包括“无，但更偏后端”这类混合输入 | 按有效 taste 处理，`has_effective_taste = true`，`max_raw_score = 114` |

无有效 taste 口径下，`user_preference = 0`，不输出或空输出 `taste_matches` / `taste_mismatches` / `user_preference_notes`，markdown 也不强制显示 Taste Fit 列。

### 4.2 candidates JSON 可选字段

在每个候选项目中增加可选字段：

```json
{
  "name": "tiny-ai-backend",
  "repo_url": "https://github.com/example/tiny-ai-backend",
  "tags": ["fastapi", "postgresql", "rag", "docker"],
  "jd_keywords": ["api", "database", "docker"],
  "matched_jd_terms": ["后端", "API", "Docker"],
  "taste_tags": ["backend", "ai-app", "local-docker", "interview-friendly"],
  "project_taste_notes": [
    "偏后端 + AI 应用形态",
    "Docker Compose 可本地 smoke test",
    "API/数据库/检索链路适合面试讲"
  ],
  "avoid_tags": ["multi-gpu"]
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `taste_tags` | `list[str]` | 否 | 项目自身可匹配的偏好标签，例如 `backend`、`ai-app`、`local-docker`、`interview-friendly` |
| `project_taste_notes` | `list[str]` | 否 | 候选项目的通用 taste 说明，例如项目形态、可演示性、运行便利性；不绑定某个具体用户，不参与脚本打分 |
| `avoid_tags` | `list[str]` | 否 | 项目自身可能让部分用户避雷的属性，例如 `pure-frontend`、`multi-gpu`、`cloud-only`、`large-dataset` |

注意：`avoid_tags` 不是“已经结合某个用户后的不匹配结果”。结合用户 taste 后的结果应写到输出字段 `taste_mismatches`。

### 4.3 输出 JSON 新增字段

有效 taste 输入时，`candidate_score.json` 中每个 candidate 的输出结构建议如下。注意字段层级：`score_breakdown` 里只新增 `user_preference`；`taste_matches`、`taste_mismatches`、`user_preference_notes` 是 candidate 顶层字段，不属于 `score_breakdown`。

```json
{
  "score": 78.95,
  "raw_score": 90,
  "max_raw_score": 114,
  "score_breakdown": {
    "jd_match": 25,
    "license": 4,
    "runnable": 20,
    "resource_fit": 10,
    "activity": 10,
    "stars": 8,
    "modification_space": 15,
    "user_preference": 8,
    "risk_penalty": -10
  },
  "taste_matches": ["backend", "local-docker", "interview-friendly"],
  "taste_mismatches": ["multi-gpu"],
  "user_preference_notes": ["符合用户偏好的本地 Docker smoke test"]
}
```

`risk_penalty` 在 `score_breakdown` 中保持负数展示，表示它已经是扣分项。内部实现可以使用正数 `risk_penalty_points`，计算时再减掉：

```text
raw_score = positive_points - risk_penalty_points
score_breakdown["risk_penalty"] = -risk_penalty_points
```

不要把 `score_breakdown["risk_penalty"]` 再代入 `- risk_penalty`，否则会把扣分错误地加回来。

## 5. 打分设计

### 5.1 原有打分

当前 `candidate_score.py` 大致为：

```text
raw_score = jd_match
          + license
          + runnable
          + resource_fit
          + activity
          + stars
          + modification_space
          - risk_penalty_points
```

其中 JD 匹配最高 30，可运行性 20，魔改空间 20，资源 / 活跃度 / stars 等作为辅助。原有正向分上限为：

```text
30 + 4 + 20 + 10 + 10 + 10 + 20 = 104
```

### 5.2 新增 user_preference

建议新增小权重：0-10 分。

```text
raw_score = jd_match
          + license
          + runnable
          + resource_fit
          + activity
          + stars
          + modification_space
          + user_preference
          - risk_penalty_points
```

设计原则：

- 无有效 taste 输入：`user_preference = 0`，排序不引入用户偏好因素。
- 有效 taste 输入：根据用户正向偏好和避雷偏好，匹配 `taste_tags`、`tags`、`avoid_tags` 等结构化字段。
- 命中用户正向偏好：加分。
- 命中用户避雷偏好：扣少量分，或计入 mismatch 解释。
- 分值上限建议 10，避免 taste 让明显差项目反超。
- `project_taste_notes` 和 `user_preference_notes` 都只用于展示解释，不参与脚本打分，避免“解释文本反过来影响分数”。

### 5.3 raw score 到 0-100 的归一化映射

新增 taste 后，raw score 的理论上限从 104 变成 114。为了让 `score` 始终落在 0-100，并且无有效 taste / 有效 taste 场景各自满分都能映射到 100，建议不再简单 clamp，而是先计算 raw score，再按对应上限归一化。

无有效 taste 场景：

```text
x 属于 [0, 104]
y 属于 [0, 100]
y = x * 100 / 104
score = round(y, 2)
```

有效 taste 场景：

```text
x 属于 [0, 114]
y 属于 [0, 100]
y = x * 100 / 114
score = round(y, 2)
```

实现建议：

```python
def normalize_score(raw_score: float, max_raw_score: float) -> float:
    x = max(0.0, min(float(raw_score), float(max_raw_score)))
    return round(x * 100 / max_raw_score, 2)
```

说明：如果希望“原来的总分 104 也映射到 100”，无有效 taste 场景的分母应为 104；如果使用 114 作为分母，则 104 只能映射到 91.23，不能满足旧满分映射到 100 的要求。`--taste` 文件为空，或内容仅等价于“无 / 都可以 / 跳过”且没有具体偏好时，也属于无有效 taste 场景，分母仍然是 104；如果文本里同时出现具体偏好，则按有效 taste 处理。

排序注意事项：`score` 改为两位小数后，排序不能再用会截断小数的 `safe_int(score)`。否则 78.95 和 78.01 会被当成同一整数分，近分候选项目的排序精度会丢。实现时应先在 `common.py` 新增 `safe_float()`，再用 `safe_float(score)` 排序；或者直接在排序处用 `float(score)` 的安全 fallback / 未截断的 `raw_score` 作为排序键。仓库目前只有 `safe_int()`，没有 `safe_float()`，如果采用 helper 方案，需要补如下函数：

```python
def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
```

### 5.4 伪代码

```python
NOOP_TASTE_TEXTS = {"", "无", "无，按 jd 推荐", "无, 按 jd 推荐", "都可以", "跳过", "none", "n/a", "no preference", "skip"}


def has_effective_taste(taste_text: str | None) -> bool:
    if taste_text is None:
        return False
    normalized = taste_text.strip().lower()
    if not normalized:
        return False
    return normalized not in NOOP_TASTE_TEXTS


def parse_user_taste(taste_text: str) -> tuple[set[str], set[str]]:
    """把用户自然语言偏好粗略拆成 prefer_tags 和 avoid_tags。

    第一版不做复杂 NLP，但需要支持常见中文短语和中英文 alias：
    - 后端 -> backend
    - AI / RAG / 大模型应用 -> ai-app
    - 本地跑通 / Docker -> local-docker
    - 适合面试讲 -> interview-friendly
    - 不想 / 不要 / 避免 + 前端 -> pure-frontend
    - 不想 / 不要 / 避免 + 多机多卡 / GPU -> multi-gpu
    """
    ...


def taste_score(candidate: dict[str, Any], taste_text: str | None) -> tuple[int, list[str], list[str], str]:
    if not has_effective_taste(taste_text):
        return 0, [], [], "no effective user preference provided"

    prefer_tags, user_avoid_tags = parse_user_taste(taste_text)

    positive_fields = [
        *normalize_list(candidate.get("taste_tags")),
        *normalize_list(candidate.get("tags")),
    ]
    project_avoid_fields = normalize_list(candidate.get("avoid_tags"))

    matches = explicit_tag_matches(positive_fields, prefer_tags)
    mismatches = explicit_tag_matches(project_avoid_fields, user_avoid_tags)

    points = min(10, len(matches) * 2) - min(4, len(mismatches) * 2)
    points = max(0, points)

    return points, matches, mismatches, f"{len(matches)} taste matches, {len(mismatches)} avoid matches"
```

现有 `tokenize()` 只识别英文 / 数字 token，不能直接覆盖“更想做后端”“不想做纯前端”“希望本地跑通”等中文表达。第一版可以复用 `normalize_list()`，但需要额外做以下至少一种处理：

- 对 taste 原文做中文 substring matching；
- 增加简单中英文 alias 表；
- 或让 agent 在调用脚本前把 taste 归一化成 `prefer_tags` / `avoid_tags`。

## 6. Agent 责任边界

### 6.1 Agent 负责

- 从用户自然语言中理解 taste。
- 区分正向偏好和避雷项，尤其是“不要 / 不想 / 避免 / 不希望”这类否定表达。
- 把 taste 写入 `taste.txt` 或对话上下文。
- 搜项目时根据 taste 初筛。
- 在 candidate JSON 中补充 `taste_tags`、`project_taste_notes`、`avoid_tags`。
- 最终输出人类可读解释。

### 6.2 脚本负责

- 读取可选 `--taste`。
- 根据显式字段做轻量匹配和排序辅助。
- 输出分数、匹配词、解释。
- 对 raw score 做 0-100 归一化，并保留必要的 `raw_score` / `max_raw_score` 方便审阅。
- 保持无有效 taste 输入时的 workflow 和 CLI 用法兼容。

## 7. 文件改动清单

建议第一版改这些文件：

| 文件 | 改动 | 当前状态 / 备注 |
| --- | --- | --- |
| `README.md` | 推荐用法加入 JD 后 taste gate、A/B/C/D 流程和 CLI 示例 | 已同步 |
| `README.en.md` | 英文同步 | 已同步 |
| `skills/shushu-internship-tool/SKILL.md` | Intake、Repo Discovery、Candidate Ranking 增加 taste 说明 | 已同步并清理过渡说明 |
| `skills/shushu-internship-tool/references/repo-selection-rubric.md` | 新增“用户偏好匹配”评分维度 | 已更新 |
| `skills/shushu-internship-tool/scripts/shushu_internship_tool/candidate_score.py` | 新增 `--taste`、`taste_score`、`normalize_score`、`raw_score`、`max_raw_score`、`safe_float` / 小数排序 | 已实现 |
| `tests/test_candidate_score.py` | 新增 taste、分数归一化和小数排序相关测试 | 已更新 |
| `reports/demo/taste.txt` | 本地 smoke test 示例 taste 输入 | 属于 `reports/` 生成物，受 `.gitignore` 忽略，不纳入本 PR |
| `docs/user-taste-preference*.md` | 设计 / TODO / README 草案 | 作为本 PR 文档纳入版本控制 |

## 8. 兼容性

- 不传 `--taste`：旧 CLI 用法兼容，排序不引入 taste 因素，分母使用 104。
- 传了 `--taste` 但文件为空、只有空白，或内容仅等价于“无 / 都可以 / 跳过”且没有具体偏好：仍按无有效 taste 处理，排序不引入 taste 因素，分母使用 104。
- 只有 `--taste` 包含有效偏好或避雷项时，才按有效 taste 处理，分母使用 114。
- 如果实现 raw score 归一化，无有效 taste 场景的 `score` 数值会从旧的简单 clamp 变成 `clamp(raw_score, 0, 104) * 100 / 104`，所以旧报表快照和精确分数断言需要更新；但 workflow 和 taste 维度不会影响旧输入。
- candidates JSON 没有 `taste_tags`：脚本回退到 `tags`；没有可匹配字段则 `user_preference = 0`。
- markdown 中的 `Taste Fit` / `Preference` 列建议只在存在有效 taste 时输出；空 `--taste` 或“无 / 都可以 / 跳过”不显示该列，减少无有效 taste 场景的文本变化。
- 当前实现会在无有效 taste 时保留 `score_breakdown.user_preference = 0`，但不输出 `taste_matches` / `taste_mismatches` / `user_preference_notes`，markdown 也不显示 Taste Fit 列。

## 9. 风险与约束

| 风险 | 处理方式 |
| --- | --- |
| 用户 taste 太模糊 | 如果用户选择 D 自定义但输入太模糊，可在本轮让用户补一句；如果用户明确选择 no 且没有具体偏好，按无有效 taste 处理 |
| taste 权重过高导致偏离 JD | 上限 10 分，硬性风险仍扣分 |
| 中文偏好和英文 tag 匹配弱 | 使用中文 substring / alias 表，或由 agent 写中英文 taste tags |
| 否定偏好被误当正向偏好 | 拆分 `prefer_tags` 和 `avoid_tags`，不要只用一组 token |
| 解释文本污染分数 | `project_taste_notes` / `user_preference_notes` 只展示，不参与打分 |
| 文档和脚本概念不一致 | README、SKILL、rubric、测试同 PR 更新 |

## 10. 验收标准

### 10.1 无有效 taste 场景

输入：旧 JD + 旧 candidates JSON。

期望：

- 命令不需要变化。
- 排序不引入 taste 因素；如果启用归一化，排序应基本保持旧结果，精确分数按 `/104` 重新计算。
- `user_preference` 为 0 或不输出。
- markdown 不强制新增 Taste Fit 列。
- 如果传入空 `--taste` 文件，或内容仅为“无 / 都可以 / 跳过”且没有具体偏好，也应满足以上无 taste 行为，并使用 104 作为分母；混合输入如“无，但更偏后端”应按有效 taste 处理。

### 10.2 有效 taste 场景

输入：JD + candidates JSON + taste.txt。

期望：

- 输出 markdown 包含 taste fit 列或说明。
- `candidate_score.json` 包含 `user_preference`、`taste_matches`、`taste_mismatches`。
- 当两个项目质量接近时，更符合用户 taste 的项目排前。
- `score` 使用 `/114` 归一化并保留两位小数。

### 10.3 不被 taste 带偏

输入：一个高风险但符合 taste 的项目，和一个 JD 匹配且可运行的项目。

期望：

- 高风险项目不能只靠 taste 成为主项目。
- 输出中明确标注风险。

### 10.4 分数归一化

输入：构造 raw score 满分项目。

期望：

- 无 taste 满分 raw score = 104，`score = 100.00`。
- 有效 taste 满分 raw score = 114，`score = 100.00`。
- 分数保留两位小数。

## 11. 推荐实施顺序

当前概念已经收口，下一步重点从“设计”转为“实现和同步”：

1. 先改 `candidate_score.py`：实现 `--taste`、`taste_score()`、`normalize_score()`、`raw_score`、`max_raw_score`、`score_breakdown.user_preference`、`safe_float()` / 小数排序。
2. 补 `tests/test_candidate_score.py`：覆盖无 taste、有 taste、空 taste、归一化、负分 clamp、小数排序、taste 不带偏。
3. 同步 `README.md` / `README.en.md` 和 `repo-selection-rubric.md`：写清 JD 后 yes/no taste gate、A/B/C/D 流程、CLI 示例和用户偏好评分维度。
4. CLI 真接上后，清理 `SKILL.md` 中“如果当前 candidate_score 尚未支持 --taste”的过渡说明，避免两套主路径并存。
5. 本地补 demo：`reports/demo/taste.txt`、带 taste 的 candidates 和 ranking 输出；`reports/` 为生成物，不纳入 PR。
6. 提交前确认 `docs/` 已进入版本控制，不误提交无关的 `OPTIMIZATION_PLAN.md`。
