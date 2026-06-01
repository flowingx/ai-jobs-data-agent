# 用户 taste / 项目偏好功能 TODO

> 目标：在用户发送 JD 后，先让用户选择是否有自己的项目偏好；选择“否”时保持原 workflow，选择“是”时展示 A/B/C/D 四个偏好选项，其中 D 是直接可填写的自定义输入框，并把最终选定的 taste 作为候选项目排序、解释和最终推荐的额外维度。

## 0. 范围确认

- [ ] 功能名暂定：用户 taste / project preference / personal preference。
- [ ] 只做“额外打分维度”，不覆盖 JD 匹配、可运行性、资源成本、面试抗压等核心维度。
- [ ] 不强制用户填写；用户跳过时维持现有 workflow。
- [ ] 不在脚本里硬编码完整岗位语义判断；岗位语义仍由 agent 提前分析并写入 candidate JSON。
- [ ] 统一命名：`score_breakdown.user_preference`、`taste_matches`、`taste_mismatches`、`user_preference_notes`；候选项目通用说明使用 `project_taste_notes`。

## 0.5 当前收口状态 / 优先级

- [x] P0：接上 `candidate_score.py`。已实现 `--taste`、`raw_score`、`max_raw_score`、`user_preference`、`taste_score()`、`safe_float()` / 小数排序，并移除旧版 `math.ceil` 整数分口径。
- [x] P1：同步 `README.md` 和 `README.en.md`。已写入 JD 后 yes/no taste gate、A/B/C/D 流程、`--taste` 用法和分数归一化说明。
- [x] P2：CLI 接上 `--taste` 后，已清理 `SKILL.md` 里的过渡说明，不再保留“旧排序 + agent 手动 tie-break”和“新 `--taste` 排序”两套主路径。
- [x] 提交前确认：`docs/` 作为本 PR 文档纳入版本控制；`OPTIMIZATION_PLAN.md` 属于后续优化计划，不纳入本 PR。

## 1. Prompt / Skill 工作流修改

- [x] 修改 `skills/shushu-internship-tool/SKILL.md` 的 JD 后 taste 选择流程。
  - [x] 用户发送 JD 后，agent 先问一次 yes/no：是否有自己的项目偏好 / taste。
  - [x] 用户选择“否 / no”时，标记为无有效 taste，继续原 workflow，不展示 A/B/C/D，不加 `user_preference`。
  - [x] 用户选择“是 / yes”时，展示 A/B/C/D 四个选项。
  - [x] 交互 gate 是显式 yes/no 选择，不解析自由文本；自定义偏好只出现在用户选择 yes 后的 D 选项里，且 D 直接呈现为输入框 / 填空项。
  - [x] A/B/C 由模型根据 JD 项目大概分类自动生成；用户已提供个人信息、技术栈、时间预算或资源条件时一并考虑，没提供时只按 JD 和保守默认生成。
  - [x] D 是用户自定义输入框 / 填空项，允许用户直接写“更想做 XXX，不想做 XXX，希望项目 XXX”。
  - [x] 如果用户在初始消息里已经主动给了 taste，也仍然先问 yes/no 确认；选择“是”才作为 D 自定义偏好，选择“否”则忽略并按 JD 默认策略推荐。
  - [x] 记录 taste 状态：已选择否、已选择 A/B/C、已选择 D 并输入、初始 taste 已确认为 D、初始 taste 已忽略；后续推荐 / 排序阶段都不再重复追问。
  - [x] 明确 taste 示例：方向、项目形态、运行深度、面试风格、避雷项。
  - [x] 明确“不要 / 不想 / 避免 / 不希望”这类表达是避雷项，不能当成正向偏好。
- [x] 修改 Repo Discovery / Candidate Ranking 描述。
  - [x] 要求 agent 在候选 JSON 中写入 `taste_tags`、`project_taste_notes`、`avoid_tags`。
  - [x] 要求输出解释“为什么符合 / 不符合用户 taste”。
  - [x] 要求 agent 尽量把用户自然语言 taste 归一化为 `prefer_tags` / `avoid_tags` 后再辅助脚本打分。
- [x] 修改 `references/repo-selection-rubric.md`。
  - [x] 新增“用户偏好匹配”评分维度。
  - [x] 新增“偏好不能压过硬性淘汰条件”的说明。

## 2. CLI / 数据结构修改

- [x] 为 `candidate_score` 增加可选参数：`--taste path/to/taste.txt`。
- [x] 明确 `--taste` 有效性：未传、文件为空、只有空白、或内容仅等价于“无 / 都可以 / 跳过 / none / no preference”且没有具体偏好时，都按无有效 taste 处理，`max_raw_score = 104`。
- [x] 只有 `--taste` 包含有效偏好或避雷项时，才按有效 taste 处理，`max_raw_score = 114`；混合输入如“无，但其实更偏后端”也算有效 taste。
- [x] 明确 `NOOP_TASTE_TEXTS` 只用于 `--taste` 文本文件兼容处理，不用于交互 gate。
- [x] 为候选项目 JSON 增加可选字段：
  - [x] `taste_tags`: 候选项目自身可匹配的偏好标签，例如 `backend`、`ai-app`、`local-docker`。
  - [x] `project_taste_notes`: 候选项目的通用 taste 说明，不绑定某个具体用户；只用于展示，不参与脚本打分。
  - [x] `avoid_tags`: 候选项目自身可能让部分用户避雷的属性，例如 `pure-frontend`、`multi-gpu`、`cloud-only`、`large-dataset`。
- [x] 在 `candidate_score.py` 中新增 `taste_score()`。
  - [x] 读取用户 taste 文本。
  - [x] 不只复用现有 `tokenize()`：现有 tokenizer 主要识别英文 token，中文 taste 需要 substring matching、alias 表，或 agent 预先归一化。
  - [x] 区分正向偏好 `prefer_tags` 和避雷项 `avoid_tags`。
  - [x] 根据候选字段 `taste_tags` / `tags` / `avoid_tags` 进行显式匹配。
  - [x] 不用 `project_taste_notes` 或 `user_preference_notes` 参与打分，避免解释文本污染分数。
  - [x] 只给小权重加分，建议 0-10 分。
  - [x] 若无有效 taste 输入，则返回 0 分且不影响排序。
- [x] 改造现有 score 计算。
  - [x] 保留 `raw_score`，不再只输出 `math.ceil(raw_score)` 后的整数分。
  - [x] 根据是否存在有效 taste 写入 `max_raw_score = 104 / 114`。
  - [x] 使用 `normalize_score(raw_score, max_raw_score)` 输出两位小数 `score`。
- [x] 在 `score_breakdown` 中新增 `user_preference`。
  - [x] 无有效 taste 时保留为 0；文档和测试统一按该口径验收。
- [x] 在 `score_reasons` 中新增 taste 解释，并在输出 candidate 顶层写入 `user_preference_notes` 作为“针对当前用户 taste 的匹配解释”。
- [x] 如果 `score` 改成两位小数，排序逻辑不要继续使用会截断小数的 `safe_int(score)`。
  - [x] 推荐在 `common.py` 新增 `safe_float(value: Any, default: float = 0.0) -> float`。
  - [x] `rank_candidates()` 使用 `safe_float(score)` 或未截断的 `raw_score` 排序，避免 78.95 和 78.01 被同样当成 78。
- [x] 在 `candidate_score.md` 表格中新增 `Preference` 或 `Taste Fit` 列。
  - [x] 建议仅在存在有效 taste 时显示该列；空 `--taste` 或“无 / 都可以 / 跳过”不显示该列，减少无有效 taste 场景输出变化。
- [x] 明确 `risk_penalty` 符号：内部可用正数 `risk_penalty_points`，但 `score_breakdown["risk_penalty"]` 展示为负数扣分项。

## 3. README / 使用说明修改

- [x] 修改 `README.md` 推荐用法。
  - [x] 替换旧的“最多 5 问 / 技术栈偏好”口径，改成 JD 后 yes/no taste gate。
  - [x] 在示例 prompt 里加入“项目偏好 / taste”。
  - [x] 说明可以不填。
  - [x] 说明用户发送 JD 后会先被问 yes/no：是否有项目偏好；选择否走原 workflow，选择是再展示 A/B/C/D 四个选项。
  - [x] 说明 A/B/C 是模型根据 JD 项目大概分类生成的推荐偏好；有用户个人信息时同时考虑，D 是直接可填写的自定义输入框。
  - [x] 增加一段示例：更想做后端、AI、能本地跑通、适合面试讲，不想做纯前端等。
  - [x] 说明明确选择 no 时不会加 taste 权重；只有选择 yes 并完成 A/B/C/D 后才会产生有效 taste。
  - [x] 在 CLI 示例里标明 `--taste` 是实现后的可选参数；如果本 PR 同时实现 CLI，则去掉“目标接口”措辞。
- [x] 同步修改 `README.en.md`。
- [x] 如果加入 CLI 参数，补充 `candidate_score --taste taste.txt` 用法。
- [x] 如果实现分数归一化，说明 `score` 是 raw score 归一化到 0-100 后的结果。

## 4. 测试

- [x] 增加单测：无有效 taste 输入时，排序不引入 taste 因素。
- [x] 增加单测：无 taste 满分 raw score = 104 时，归一化 `score = 100.00`。
- [x] 增加单测：`--taste` 文件为空、只有空白、或内容仅为“无 / 都可以 / 跳过”且没有具体偏好时，按无有效 taste 处理并使用 104 分母。
- [x] 增加单测：`--taste` 文本文件中的混合输入如“无，但其实更偏后端”应按有效 taste 处理；该规则不属于交互 gate。
- [x] 增加单测：有效 taste 满分 raw score = 114 时，归一化 `score = 100.00`。
- [x] 增加单测：raw score 为负时，clamp 后 `score = 0.00`。
- [x] 增加单测：score 为两位小数时排序不丢精度，例如 78.95 应排在 78.01 前面。
- [x] 增加单测：两个项目分数接近时，taste 匹配项目排前。
- [x] 增加单测：taste 只作为小权重，不能让明显不可运行 / 高风险项目反超优质项目。
- [x] 增加单测：中文 taste 能匹配常见 alias，例如“后端”“本地跑通”“适合面试讲”。
- [x] 增加单测：否定偏好不会被误加分，例如“不想做纯前端”不应给纯前端项目加正向分。
- [x] 增加单测：markdown 输出在有效 taste 时包含 taste fit 信息，无有效 taste 时不强制新增列。
- [x] 运行完整测试：`.venv/bin/python -m pytest`。

## 5. Demo / 验收

- [x] 准备一个 JD 示例，例如后端 / AI / 数据工程三选一。
- [x] 跑一次不带 taste 的排序，确认 workflow 和排序逻辑兼容。
- [x] 跑一次带 taste 的排序，确认输出解释包含用户偏好。
- [x] 检查排序结果是否仍满足：JD 匹配、可运行、低资源、面试可讲。
- [x] 检查输出 JSON 是否包含 `raw_score`、`max_raw_score`、归一化后的 `score`。

## 6. 当前最短改动顺序 / PR 拆分建议

### PR 1：candidate_score CLI 支持 taste（高优先级）

- [x] 增加 `--taste` 参数和 scoring 字段。
- [x] 增加 `taste_score()`、`normalize_score()`、`safe_float()`。
- [x] 输出 `raw_score`、`max_raw_score`、`score_breakdown.user_preference`、`taste_matches`、`taste_mismatches`、`user_preference_notes`。
- [x] 修复小数分排序：不要继续用 `safe_int(score)` 截断。
- [x] 增加测试。
- [x] 验收：无有效 taste 兼容，有效 taste 可解释；CLI 示例真实可运行。

### PR 2：README / Skill / Rubric 同步（中优先级）

- [x] 更新 `README.md`、`README.en.md`，让外部用户看到 JD 后 yes/no taste gate 和 A/B/C/D 流程。
- [x] 更新 `repo-selection-rubric.md`，加入“用户偏好匹配”维度。
- [x] CLI 真接上后，删除或改写 `SKILL.md` 里的过渡说明，避免“旧排序 + agent 手动 tie-break”和“新 `--taste` 排序”两套主路径并存。
- [x] 验收：README、SKILL、rubric、CLI 用法口径一致。

### PR 3：示例报告和 demo（低优先级）

- [x] 本地生成 `reports/demo/taste.txt`、带 taste 的 candidates 和 ranking 输出用于 smoke test。
- [x] 注意：`reports/` 属于生成物目录，受 `.gitignore` 忽略，不纳入本 PR。

### 提交前检查

- [x] `docs/` 已作为本 PR 文档准备纳入版本控制。
- [x] 不误提交无关的 `OPTIMIZATION_PLAN.md`。
- [x] 运行完整测试：`.venv/bin/python -m pytest`。

## 7. 打分归一化

- [x] 不再只做 0-100 clamp；先计算 raw score，再按场景归一化到 0-100。
- [x] 无有效 taste 场景：原有正向满分为 104，所以：

  ```text
  x 属于 [0, 104]
  y 属于 [0, 100]
  y = x * 100 / 104
  score = round(y, 2)
  ```

- [x] 有效 taste 场景：新增 `user_preference` 后正向满分为 114，所以：

  ```text
  x 属于 [0, 114]
  y 属于 [0, 100]
  y = x * 100 / 114
  score = round(y, 2)
  ```

- [x] 实现时先把 raw score 限制到对应区间，再保留两位小数：

  ```python
  x = max(0, min(raw_score, max_raw_score))
  score = round(x * 100 / max_raw_score, 2)
  ```

- [x] 注意：如果希望原来的总分 104 映射到 100，无有效 taste 场景分母应为 104；使用 114 会让 104 映射为 91.23。空 `--taste`，或仅包含“无 / 都可以 / 跳过”且没有具体偏好，也属于无有效 taste 场景。

## 8. 完成定义

- [x] 用户只给 JD 时，工具仍会按旧 workflow 进行简短 intake。
- [x] 用户给了 taste 时，输出项目推荐能说明“为什么更符合你的偏好”。
- [x] 排序结果中可以看到 `user_preference` 分数或解释。
- [x] `score` 是 raw score 映射到 0-100 后的两位小数。
- [x] 不会因为 taste 把低质量、高风险、不可运行项目推荐成主项目。
- [x] README、skill、rubric、测试全部同步。
