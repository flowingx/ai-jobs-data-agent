# 鼠鼠实习妙妙工具

<p align="center">
  <img src="assets/logo.svg" alt="鼠鼠实习妙妙工具 Logo" width="400">
</p>

<h2 align="center">SIT —— shushu internship tool</h2>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-v1.0.0-brightgreen">
  <img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-blue">
  <img alt="Audience" src="https://img.shields.io/badge/audience-CS%20Internship-orange">
  <img alt="Workflow" src="https://img.shields.io/badge/workflow-Job%20Description%20to%20Interview-purple">
</p>

> 把岗位描述变项目，把项目变简历，把简历变面试。



鼠鼠实习妙妙工具是一个AI驱动的实习项目准备工具包（skill）：把目标 JD（Job Description，岗位描述/招聘需求）快速转成能投递、能面试、能讲清的项目素材闭环。这里的 JD 通常包括岗位职责、任职要求、技术栈、业务方向、地点、学历/毕业时间限制等信息。

它适合后端、前端、全栈、移动端、测试开发、数据工程、云原生/DevOps、安全、系统、AI/算法等计算机方向，旨在帮 0 经验或低经验候选人（鼠鼠）用最短路径完成：选题、理解、复现、简历表达、面试拷问和展示材料。

如果只给 JD（岗位描述/招聘需求），工具会先补一个短 intake：你的知识水平、技术栈偏好、时间预算、资源条件，以及是否要完整跑项目。默认不是一上来就完整跑到底，而是先选择运行深度。

> 欢迎加入鼠鼠实习就业交流群，QQ群号：976187338。

## 它能做什么

- 根据 JD（岗位描述/招聘需求）找 2-3 个合适的 GitHub 项目，并按岗位匹配度、上手速度、可讲亮点、运行成本和改造空间排序。
- 审计已 clone 的项目，生成 `audit.json`、`overview.md` 和 `overview.html`，帮助快速理解代码结构、入口、依赖、API/页面/数据流/任务流。
- 规划 baseline run：优先本地最小路径跑通，不够再设计云服务器、数据库、对象存储、GPU/AutoDL 或其他远程环境方案。
- 推进可面试的改造点：加 API、加页面、换数据库、加缓存、加测试、加监控、加 CI/CD、改数据流、优化性能、补 demo 或做 AI/算法实验。
- 生成面试包：STAR 简历项目、核心代码讲解、面试官拷问 Q&A、PPT 提示词和投递检查表。

## 推荐用法

把目标 JD（岗位描述/招聘需求）和自己的基础情况发给 AI 助手，并说明想要的运行深度：

```text
使用鼠鼠实习妙妙工具，根据下面这份 JD（岗位描述/招聘需求）帮我规划一个能投递、能面试、能讲清的计算机实习项目。

我的情况：
- 当前水平：
- 熟悉语言/框架：
- 时间预算：
- 本地/远程资源：
- 希望运行深度：interview-only / smoke-test / local-full-run / remote-full-run

JD（岗位描述/招聘需求）：
...
```

如果你暂时不知道怎么填，可以只给 JD（岗位描述/招聘需求），让工具先问你几个问题。

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

给候选项目排序：

```bash
python -m shushu_internship_tool.candidate_score --jd jd.txt --candidates candidates.json --out reports/ranking
```

生成面试材料包骨架：

```bash
python -m shushu_internship_tool.interview_pack --project-notes reports/audit --out reports/interview-pack
```

安装后也可以使用命令入口：

```bash
shushu-repo-audit --repo /path/to/repo --out reports/audit --name my-project
shushu-candidate-score --jd jd.txt --candidates candidates.json --out reports/ranking
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
    "risk_notes": ["database migration needs setup"]
  }
]
```

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
