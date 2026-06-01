# 鼠鼠实习妙妙工具

<p align="center">
  <img src="assets/logo.svg" alt="鼠鼠实习妙妙工具 Logo" width="400">
</p>

<h2 align="center">SIT —— shushu internship tool</h2>

<p align="center">
  中文 | <a href="README.en.md">English</a>
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-v1.0.0-brightgreen">
  <img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-blue">
  <img alt="Audience" src="https://img.shields.io/badge/audience-CS%20Internship-orange">
  <img alt="Workflow" src="https://img.shields.io/badge/workflow-Job%20Description%20to%20Interview-purple">
</p>

> 把岗位描述变项目，把项目变简历，把简历变面试。



鼠鼠实习妙妙工具是一个AI驱动的实习项目准备工具包（skill）：把目标 JD（Job Description，岗位描述/招聘需求）快速转成能投递、能面试、能讲清的项目素材闭环。这里的 JD 通常包括岗位职责、任职要求、技术栈、业务方向、地点、学历/毕业时间限制等信息。

它适合后端、前端、全栈、移动端、测试开发、数据工程、云原生/DevOps、安全、系统、AI/算法等计算机方向，旨在帮 0 经验或低经验候选人（鼠鼠）用最短路径完成：选题、理解、复现、简历表达、面试拷问和展示材料。

如果只给 JD（岗位描述/招聘需求），工具会先做 JD 初步理解，然后触发一次项目偏好 / taste 的 yes/no gate：你可以选择“没有偏好，按 JD 和默认稳妥策略推荐”，也可以选择“有偏好”并从 A/B/C/D 中选择或自定义。之后工具再补一个短 intake：你的知识水平、技术栈现状、时间预算、资源条件，以及希望运行到什么深度。

> 欢迎加入鼠鼠实习就业交流群，QQ群号：976187338。

## 强联动新项目：VibeResume

**[VibeResume](https://github.com/LiuMengxuan04/vibe-resume)** 是一个 AI 友好、网页优先、可稳定导出 PDF 的简历模板：把简历维护成 `HTML + CSS`，让 AI 直接改内容和排版，再一键导出一页 PDF。

它可以作为 SIT 的“最后一公里”联动项目：SIT 负责把 JD 转成项目与面试材料，VibeResume 负责把最终简历内容沉淀成漂亮、可版本管理、可持续迭代的网页简历。

## 友情链接与灵感来源

- 友情链接：[鼠鼠实习简历优化器](https://github.com/Sunanzhe2004/shushu-internship-resume-optimizer)：把实习代码仓库、项目总结和业务背景材料整理成简历成果、STAR 草稿和面试复盘材料。
- 友情链接：[ProjectProof](https://github.com/YingaoWang-casia/shushu-ProjectProof)：面向单薄实习和 AI 项目的证据化审核与面试追问补强工具，帮助把真实经历讲深讲透。
- 灵感来源：[leilon](https://github.com/leilon)，本 skill 的想法受到其相关实践与分享启发。

## 它能做什么

- 根据 JD（岗位描述/招聘需求）找 2-3 个合适的 GitHub 项目，并按岗位匹配度、上手速度、可讲亮点、运行成本和改造空间排序。
- 审计已 clone 的项目，生成 `audit.json`、`overview.md` 和 `overview.html`，帮助快速理解代码结构、入口、依赖、API/页面/数据流/任务流。
- 规划 baseline run：优先本地最小路径跑通，不够再设计云服务器、数据库、对象存储、GPU/AutoDL 或其他远程环境方案。
- 推进可面试的改造点：加 API、加页面、换数据库、加缓存、加测试、加监控、加 CI/CD、改数据流、优化性能、补 demo 或做 AI/算法实验。
- 生成面试包：STAR 简历项目、核心代码讲解、面试官拷问 Q&A、PPT 提示词和投递检查表。

## 推荐用法

把目标 JD（岗位描述/招聘需求）和自己的基础情况发给 AI 助手，并说明想要的运行深度；如果你已经有明确项目偏好 / taste，也可以直接写在初始输入里，但工具仍会先做一次 yes/no 确认，确认后才把它作为 D 自定义偏好使用：

```text
使用鼠鼠实习妙妙工具，根据下面这份 JD（岗位描述/招聘需求）帮我规划一个能投递、能面试、能讲清的计算机实习项目。

我的情况：
- 当前水平：学过课程但项目少
- 熟悉语言/框架：Python、FastAPI、一点 React
- 时间预算：2 天
- 本地/远程资源：本地电脑 + Docker，无 GPU
- 希望运行深度：interview-only / smoke-test / local-full-run / remote-full-run
- 项目偏好 / taste：更想做后端 + AI 应用；希望能本地跑通，适合面试讲；不想做纯前端，不想依赖多机多卡或复杂云服务。

JD（岗位描述/招聘需求）：
...
```

如果你暂时没有偏好，可以写“项目偏好 / taste：无，按 JD 推荐”，或者只给 JD。工具会在 JD 初步分析后一定先问一次 yes/no：你是否有自己的项目偏好 / taste？如果你已经在初始输入里写了偏好，工具会先确认是否将这段内容作为 D 自定义偏好。

- 选择“没有 / no”：继续原 workflow，只根据 JD、技能匹配、可运行性、资源成本、项目风险和面试可讲性推荐，不加 taste 权重；如果初始输入里写过偏好，也会忽略。
- 选择“有 / yes”：工具会展示 A/B/C/D 四个选项。
  - A/B/C：模型根据 JD 对应的项目大概分类动态生成；如果你提供了个人信息、技术栈、时间预算或资源条件，就同时考虑这些信息；没提供则只按 JD 和保守默认生成。
  - D：一个直接可填写的自定义输入框 / 填空项，例如 `D. ________`；你可以直接写“更想做后端 + AI 应用，不想做纯前端，希望 Docker 本地跑通，适合面试讲”。如果初始输入里已有偏好且你确认使用，D 会沿用这段内容。

注意，“不要 / 不想 / 避免 / 不希望”这类表达会被当成避雷项，而不是正向偏好。

## Star 趋势

[![Star History Chart](https://api.star-history.com/svg?repos=LiuMengxuan04/shushu-internship-tool&type=Date)](https://www.star-history.com/#LiuMengxuan04/shushu-internship-tool&Date)

## 安装本地脚本

```bash
cd shushu-internship-tool
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

## 脚本

审计本地项目：

```bash
python -m shushu_internship_tool.repo_audit --repo /path/to/repo --out reports/audit --name my-project
```

给候选项目排序（无 taste，兼容旧用法）：

```bash
python -m shushu_internship_tool.candidate_score --jd jd.txt --candidates candidates.json --out reports/ranking
```

给候选项目排序（带可选项目偏好 / taste）：

```bash
python -m shushu_internship_tool.candidate_score --jd jd.txt --candidates candidates.json --taste taste.txt --out reports/ranking
```

`candidate_score` 会先计算 `raw_score`，再按 `max_raw_score` 归一化到 0-100：无有效 taste 时分母为 104；有效 taste 时新增 `user_preference` 小权重，分母为 114。`--taste` 未传、文件为空、只有空白，或内容仅等价于“无 / 都可以 / 跳过 / none / no preference”时，都按无有效 taste 处理。

生成面试材料包骨架：

```bash
python -m shushu_internship_tool.interview_pack --project-notes reports/audit --out reports/interview-pack
```

安装后也可以使用命令入口：

```bash
shushu-repo-audit --repo /path/to/repo --out reports/audit --name my-project
shushu-candidate-score --jd jd.txt --candidates candidates.json --out reports/ranking
shushu-candidate-score --jd jd.txt --candidates candidates.json --taste taste.txt --out reports/ranking
shushu-interview-pack --project-notes reports/audit --out reports/interview-pack
```

## 候选项目 JSON 示例

```json
[
  {
    "name": "tiny-ticket-system",
    "repo_url": "https://github.com/example/tiny-ticket-system",
    "license": "MIT",
    "stars": 320,
    "last_commit": "2026-04-20",
    "tags": ["fastapi", "postgresql", "docker", "rest-api"],
    "jd_keywords": ["backend", "api design", "database", "docker"],
    "matched_jd_terms": ["后端开发", "接口设计", "数据库", "容器化部署"],
    "runnable": true,
    "compute": "local_docker",
    "mod_ideas": ["add JWT auth", "add Redis cache", "add integration tests"],
    "risk_notes": ["database migration needs setup"],
    "taste_tags": ["backend", "local-docker", "interview-friendly", "api", "database"],
    "project_taste_notes": [
      "偏后端工程落地形态",
      "Docker 本地 smoke test 路径清楚",
      "API / 数据库 / 缓存改造适合面试讲"
    ],
    "avoid_tags": ["cloud-heavy"]
  }
]
```

候选项目的 taste 字段都是可选字段：`taste_tags` 用于匹配用户正向偏好，`avoid_tags` 表示项目自身可能让部分用户避雷的属性，`project_taste_notes` 只做展示说明，不参与脚本打分。

## 求职效率原则

- 第一目标是帮候选人尽快拿到面试：JD（岗位描述/招聘需求）命中、项目标题、4-5 行简历表达、面试问答要优先产出。
- 不要把时间耗在“完整复现论文级结果”或“重写整个系统”上；先做 smoke test、核心流程理解和能讲清的 demo/改造点。
- 魔改不追求大而全，优先选面试官听得懂、自己说得明白、能快速推进的增量，比如 API、页面、测试、缓存、部署、性能、数据处理或算法实验。
- 指标有就写具体数字；暂时没有指标就改写成工程产出、方法理解、系统设计、实验设计和下一步计划。
- 面试准备比完美实验更重要：让 AI 助手扮演面试官反复拷问，直到能讲清 input/output、方法选择、失败原因和改进方向。

## 运行深度

- `interview-only`：不完整跑项目，优先做项目选择、简历、核心代码阅读路线、面试 Q&A、PPT 提示词。
- `smoke-test`：跑最小可运行路径，只证明项目能启动或核心流程能走通。
- `local-full-run`：在本地完整跑通 baseline/demo，并尽量产出可展示结果。
- `remote-full-run`：使用云服务器、数据库、GPU 或其他远程环境完整跑通，适合时间和预算更充足的情况。

## 开发

```bash
cd shushu-internship-tool
. .venv/bin/activate
pytest
```

## License

Apache-2.0
