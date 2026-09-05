---
description: |
  ContentFlow AI 全流程项目学习与开发
  Skill。从项目立项、需求分析、用户场景、
  竞品调研、PRD、MVP、原型、技术选型和架构设计开始，经过纯 Python MVP、
  LLM API、Prompt Engineering、Structured Output、LangGraph、Research
  Agent、 Tool Calling、RAG、Quality Loop、Adapter、Visual
  Agent、Streamlit、SQLite，
  最终完成测试、Debug、部署、GitHub、项目报告、Demo、答辩、简历与面试复盘。
  核心目标是让开发者边做边学，真正经历一次完整 AI 应用项目生命周期。
name: contentflow-ai-full-project-coach
---

# ContentFlow AI Full Project Coach

## 0. Skill 的使用方式

本 Skill 不只是"教你写代码"，而是带开发者从 0 到 1 完整经历一次 AI
项目：

``` text
发现问题
  ↓
项目立项
  ↓
需求分析
  ↓
用户与场景
  ↓
竞品/现有方案分析
  ↓
PRD
  ↓
MVP
  ↓
用户流程
  ↓
原型
  ↓
技术需求拆解
  ↓
技术选型
  ↓
系统架构
  ↓
项目初始化
  ↓
纯 Python MVP
  ↓
LLM 能力开发
  ↓
Workflow
  ↓
LangGraph 重构
  ↓
Agent / Tool Calling
  ↓
RAG
  ↓
前端 / 数据库
  ↓
测试
  ↓
Debug
  ↓
优化
  ↓
部署
  ↓
GitHub / README
  ↓
Demo / 项目报告
  ↓
答辩
  ↓
项目复盘
  ↓
简历 / 面试
```

## 核心教学原则

每进入一个阶段，都按照：

``` text
为什么要做？
 ↓
这个阶段解决什么问题？
 ↓
需要学习什么？
 ↓
设计方案
 ↓
自己实现
 ↓
运行
 ↓
发现问题
 ↓
Debug
 ↓
测试
 ↓
总结
 ↓
Git Commit
```

不要直接跳到最终代码。

AI 编程工具是 Pair Programmer，不是项目代写者。

------------------------------------------------------------------------

# 第一部分：项目立项

## Step 1：明确项目主题

项目暂定：

**ContentFlow AI ------ 基于大语言模型与 Agent Workflow
的智能内容创作系统**

项目核心目标：

用户提供一个主题、目标受众和内容需求，系统通过 AI Workflow 完成：

``` text
主题
 ↓
内容策划
 ↓
资料研究
 ↓
内容生成
 ↓
质量审核
 ↓
自动优化
 ↓
多平台适配
 ↓
视觉内容规划
 ↓
最终内容包
```

## Step 2：写项目背景

开发者必须自己回答：

1.  为什么想做这个项目？
2.  现实中存在什么问题？
3.  现有内容创作流程哪里效率低？
4.  AI 在其中能够解决什么？
5.  为什么这个问题值得做成软件？

输出：

`docs/01-project-background.md`

------------------------------------------------------------------------

# 第二部分：需求分析

## Step 3：确定目标用户

不要写"所有人"。

先确定 2～3 类核心用户，例如：

-   大学生
-   内容创作者
-   新媒体/运营人员

对每类用户分析：

``` text
用户是谁？
 ↓
什么时候会使用？
 ↓
现在怎么完成任务？
 ↓
哪里最麻烦？
 ↓
ContentFlow AI 能帮什么？
```

输出：

`docs/02-user-analysis.md`

## Step 4：用户痛点分析

区分：

**用户痛点** 和 **产品功能**。

例如：

用户痛点：

> 从主题到最终文章需要经历查资料、整理、写作和修改，流程长且重复。

不是：

> 用户需要一个 AI 写文章按钮。

后者是解决方案，不是痛点。

至少分析：

-   时间成本
-   信息搜集成本
-   内容结构困难
-   内容质量不稳定
-   多平台重复改写
-   配图寻找成本

## Step 5：用户场景

写 3～5 个真实场景。

格式：

``` text
角色：
目标：
触发条件：
操作：
期望结果：
```

示例：

``` text
角色：大学生
目标：完成一篇科普内容
触发：只有一个选题，没有完整资料
操作：输入主题、受众和内容类型
结果：获得有资料依据的文章及 PPT/短视频脚本
```

## Step 6：用户故事

使用：

``` text
作为 [用户]
我希望 [完成某件事]
从而 [获得价值]
```

例如：

> 作为大学生，我希望输入一个主题后自动获得内容规划，从而减少自己从零搭建文章结构的时间。

------------------------------------------------------------------------

# 第三部分：竞品与现有方案分析

## Step 7：竞品/替代方案调研

目的不是为了写漂亮表格，而是回答：

> 为什么还需要 ContentFlow AI？

调研维度：

-   现有 AI 聊天工具
-   AI 写作工具
-   AI Research 工具
-   AI 内容生产工具

比较：

``` text
产品
核心能力
使用流程
优势
不足
ContentFlow 可以学习什么
ContentFlow 如何差异化
```

最终总结项目差异点，例如：

> 不只是一次性生成内容，而是 Plan → Research → Write → Review → Adapt
> 的可观察 Workflow。

输出：

`docs/03-competitor-analysis.md`

------------------------------------------------------------------------

# 第四部分：PRD

## Step 8：编写 PRD

PRD 至少包含：

``` text
1. 项目背景
2. 产品目标
3. 目标用户
4. 用户痛点
5. 使用场景
6. 用户故事
7. 产品流程
8. 功能需求
9. 功能优先级
10. MVP
11. 非功能需求
12. 异常场景
13. 验收标准
14. 后续版本规划
```

输出：

`docs/04-PRD.md`

------------------------------------------------------------------------

# 第五部分：功能拆解

## Step 9：建立功能清单

例如：

``` text
ContentFlow AI

├── 创作配置
│   ├── 主题
│   ├── 目标受众
│   ├── 内容类型
│   └── 输出形式
│
├── 内容策划
│   └── Planner
│
├── Research
│   ├── Query Planning
│   ├── Search
│   └── Research Context
│
├── 内容生成
│   ├── Writer
│   └── Rewrite
│
├── 质量控制
│   ├── Reviewer
│   └── Quality Router
│
├── 内容适配
│   └── Adapter
│
├── Visual
│   └── Visual Agent
│
└── 项目管理
    ├── 历史记录
    └── 内容版本
```

------------------------------------------------------------------------

# 第六部分：MVP 定义

## Step 10：确定 MVP

使用 MoSCoW 或类似方式区分：

### Must Have

-   输入主题
-   Planner
-   Writer
-   Reviewer
-   Rewrite
-   最终结果展示

### Should Have

-   Research
-   LangGraph
-   Structured Output
-   内容适配

### Could Have

-   RAG
-   Visual Agent
-   自动配图
-   PPT

### Won't Have（当前版本）

-   完整自动视频生产
-   复杂多用户系统
-   大规模云端部署

第一版 MVP：

``` text
Topic
 ↓
Planner
 ↓
Writer
 ↓
Reviewer
 ↓
Rewrite（需要时）
 ↓
Final
```

必须先让 MVP 完整跑通，再扩展。

------------------------------------------------------------------------

# 第七部分：用户流程设计

## Step 11：画 User Flow

例如：

``` text
打开系统
 ↓
输入主题
 ↓
选择目标用户
 ↓
选择内容类型
 ↓
开始创作
 ↓
AI规划
 ↓
AI生成
 ↓
AI审核
 ↓
是否通过？
 ↙       ↘
否        是
↓          ↓
优化      输出
```

输出：

`docs/05-user-flow.md`

------------------------------------------------------------------------

# 第八部分：原型设计

## Step 12：使用 Figma / Axure 画原型

至少设计：

### 页面 1：首页

-   Topic
-   Audience
-   Content Type
-   Output Type
-   Start

### 页面 2：Workflow

显示：

``` text
✓ 内容策划
✓ 资料研究
→ 正在生成
○ AI审核
○ 内容适配
```

### 页面 3：结果页

显示：

-   Content Plan
-   Research Sources
-   Draft
-   Review Score
-   Final Content
-   Adapter Result

### 页面 4：历史项目

显示：

-   Topic
-   Date
-   Status
-   Score

原型完成后检查：

> 每个页面元素是否都对应一个真实需求？

------------------------------------------------------------------------

# 第九部分：验收标准

## Step 13：需求转验收标准

每个核心功能写 Acceptance Criteria。

例如 Planner：

``` text
Given 用户输入有效主题
When 点击开始创作
Then 系统返回包含 audience、tone、sections 的结构化 Content Plan
```

Reviewer：

``` text
Given 已生成 Draft
When Reviewer 执行
Then 返回结构化评分、问题和修改建议
```

这样后面测试不会脱离需求。

------------------------------------------------------------------------

# 第十部分：技术需求拆解

## Step 14：从功能反推技术

不要先决定"我要用 LangGraph"。

先建立：

  需求         技术问题                 候选方案
  ------------ ------------------------ --------------------
  AI内容规划   如何调用模型             LLM API
  稳定字段     如何避免自然语言乱输出   Structured Output
  Workflow     如何管理流程             Python / LangGraph
  Research     如何获取外部信息         Search Tool
  基于资料写   如何检索相关上下文       RAG
  历史记录     如何保存项目             SQLite
  UI           如何快速开发 Web 页面    Streamlit

输出：

`docs/06-technical-requirements.md`

------------------------------------------------------------------------

# 第十一部分：技术选型

## Step 15：确定技术栈

推荐：

``` text
Language        Python
UI              Streamlit
LLM             LLM API
Schema          Pydantic
Workflow        Python → LangGraph
Agent           Tool Calling Agent
RAG             Embedding + FAISS/Chroma
Database        SQLite
Version Control Git / GitHub
```

对每项技术回答：

> 为什么选它，而不是其他方案？

输出：

`docs/07-tech-selection.md`

------------------------------------------------------------------------

# 第十二部分：系统架构设计

## Step 16：画架构

``` text
                     USER
                      ↓
                Streamlit UI
                      ↓
               Business Layer
                   Python
                      ↓
                LangGraph
                      ↓
       ┌──────────────┼──────────────┐
       ↓              ↓              ↓
    LLM Nodes       Agents         Router
       ↓              ↓
    LLM API          Tools
                      ↓
           ┌──────────┼──────────┐
           ↓          ↓          ↓
         Search      RAG       Image
                      ↓
              Data / Storage
              SQLite + Vector DB
```

明确：

-   Streamlit = UI
-   Python = 业务逻辑
-   LangGraph = AI Workflow 编排
-   LLM = 推理与生成
-   Tool = 外部能力
-   SQLite/Vector DB = 数据层

输出：

`docs/08-architecture.md`

------------------------------------------------------------------------

# 第十三部分：数据流设计

## Step 17：定义 State

ContentFlow State：

``` text
topic
audience
content_type
output_type

plan
research_results
research_context

draft
review
rewrite_count

final_content
adapted_content
visual_assets

errors
status
```

画出：

``` text
USER INPUT
 ↓
State.topic
 ↓
Planner
 ↓
State.plan
 ↓
Research
 ↓
State.research
 ↓
Writer
 ↓
State.draft
 ↓
Reviewer
 ↓
State.review
```

------------------------------------------------------------------------

# 第十四部分：项目工程初始化

## Step 18：创建 Git 仓库

第一天开始使用 Git。

建议结构：

``` text
contentflow-ai/
├── app.py
├── src/
│   ├── nodes/
│   ├── agents/
│   ├── tools/
│   ├── rag/
│   ├── workflow/
│   ├── models/
│   ├── database/
│   └── utils/
├── tests/
├── docs/
├── prompts/
├── data/
├── .env.example
├── requirements.txt
└── README.md
```

创建基础分支和 Commit。

------------------------------------------------------------------------

# 第十五部分：环境与 API

## Step 19：建立开发环境

学习：

-   Python 虚拟环境
-   pip
-   requirements.txt
-   环境变量
-   `.env`
-   API Key 安全

禁止把真实 API Key 提交到 Git。

## Step 20：第一次 LLM API 调用

只完成：

``` text
Python
 ↓
LLM API
 ↓
Hello / Simple Prompt
 ↓
Response
```

此阶段学习：

-   API
-   HTTP Request
-   Response
-   JSON
-   Status Code
-   Timeout
-   Authentication

------------------------------------------------------------------------

# 第十六部分：纯 Python MVP

## Step 21：Planner

``` text
Topic
 ↓
Planner Prompt
 ↓
LLM
 ↓
Content Plan
```

先能运行，再优化。

## Step 22：Writer

``` text
Plan
 ↓
Writer
 ↓
Draft
```

## Step 23：Reviewer

``` text
Draft
 ↓
Reviewer
 ↓
Score + Problems
```

## Step 24：Rewrite

``` python
plan = planner(topic)
draft = writer(plan)
review = reviewer(draft)

if review.score < 80:
    draft = rewrite(draft, review)
```

到这里形成第一版真正可运行 MVP。

------------------------------------------------------------------------

# 第十七部分：Prompt Engineering

## Step 25：建立 Prompt 文件

不要把所有 Prompt 写死在业务代码里。

``` text
prompts/
├── planner.md
├── writer.md
├── reviewer.md
├── rewrite.md
└── adapter.md
```

## Step 26：Prompt 迭代

执行：

``` text
V1
 ↓
测试集
 ↓
记录问题
 ↓
V2
 ↓
再次测试
 ↓
V3
```

记录：

-   输出格式正确率
-   内容质量
-   重复问题
-   幻觉
-   指令遵循

------------------------------------------------------------------------

# 第十八部分：Structured Output

## Step 27：Pydantic Schema

Planner 示例：

``` json
{
  "topic": "...",
  "audience": "...",
  "tone": "...",
  "sections": []
}
```

Reviewer：

``` json
{
  "score": 85,
  "accuracy": 82,
  "logic": 90,
  "readability": 87,
  "problems": []
}
```

学习：

-   Schema
-   Validation
-   Parsing
-   Retry
-   Invalid JSON

------------------------------------------------------------------------

# 第十九部分：Streamlit MVP

## Step 28：接入 UI

完成：

``` text
输入
 ↓
开始创作
 ↓
调用 Python Workflow
 ↓
显示 Plan
 ↓
显示 Draft
 ↓
显示 Review
 ↓
显示 Final
```

此时得到第一个可以 Demo 的版本。

------------------------------------------------------------------------

# 第二十部分：为什么重构 LangGraph

## Step 29：先发现纯 Python 的问题

随着功能增加：

``` text
Research
Rewrite Loop
Conditional Routing
Shared State
Tool Calling
```

纯 Python 开始出现：

-   if/else 增多
-   状态分散
-   流程难观察
-   循环难维护

此时才引入 LangGraph。

必须能够回答：

> LangGraph 解决了当前项目中的什么工程问题？

------------------------------------------------------------------------

# 第二十一部分：LangGraph

## Step 30：学习 State / Node / Edge

映射：

``` text
LangGraph Graph = ContentFlow Workflow
State           = 项目共享数据
Node            = Planner / Writer / Reviewer
Edge            = Planner → Writer
Conditional Edge= Review → Rewrite / Pass
Loop            = Rewrite → Review
```

## Step 31：重构基础 Graph

``` text
START
 ↓
Planner
 ↓
Writer
 ↓
Reviewer
 ↓
Quality Router
 ↙          ↘
Rewrite      Pass
 ↓            ↓
Reviewer    Adapter
              ↓
             END
```

先不要加入 Agent。

------------------------------------------------------------------------

# 第二十二部分：Research Agent

## Step 32：为什么需要 Agent

问题：

> Writer 需要可靠资料，而不同主题需要搜索不同信息。

Research 无法完全写死成固定步骤。

因此设计 Research Agent：

``` text
分析任务
 ↓
发现信息缺口
 ↓
决定搜索 Query
 ↓
选择 Tool
 ↓
执行
 ↓
观察结果
 ↓
资料够吗？
 ↙      ↘
否       是
↓         ↓
继续     Finish
```

## Step 33：Tool Calling

Research Agent 可拥有：

-   Search Tool
-   Web Reader Tool
-   Knowledge Retrieval Tool

学习：

-   Tool Schema
-   Function Calling
-   Tool Result
-   Agent Loop
-   Max Iterations
-   Timeout

------------------------------------------------------------------------

# 第二十三部分：RAG

## Step 34：明确 RAG 解决的问题

不是为了简历。

问题是：

> Writer 如何基于已经获取的资料写，而不是完全依赖模型记忆？

## Step 35：逐步实现

``` text
Document
 ↓
Clean
 ↓
Chunk
 ↓
Embedding
 ↓
Vector DB
 ↓
Query Embedding
 ↓
Similarity Search
 ↓
Top-K
 ↓
Context
 ↓
Writer
```

学习：

-   Chunk Size
-   Overlap
-   Embedding
-   Vector
-   Similarity
-   Top-K
-   FAISS / Chroma

## Step 36：RAG Evaluation

建立固定问题集。

比较：

-   无 RAG
-   有 RAG
-   不同 Chunk Size
-   不同 Top-K

记录效果。

------------------------------------------------------------------------

# 第二十四部分：完整 Workflow

## Step 37：接入 Research

``` text
START
 ↓
Planner
 ↓
Research Agent
 ↓
Writer
 ↓
Reviewer
 ↓
Quality Router
```

------------------------------------------------------------------------

# 第二十五部分：Quality Loop

## Step 38：Reviewer 评价维度

例如：

``` text
事实依据
逻辑结构
可读性
受众匹配
内容完整性
```

## Step 39：Router

``` text
事实依据不足
 ↓
Research

写作质量不足
 ↓
Rewrite

达到标准
 ↓
Pass
```

必须限制：

``` text
max_research_count
max_rewrite_count
```

避免无限循环。

------------------------------------------------------------------------

# 第二十六部分：Adapter

## Step 40：多平台内容适配

``` text
Final Content
 ↓
Adapter
 ├── 长文章
 ├── 社交媒体文案
 ├── PPT 大纲
 └── 短视频脚本
```

目标明确时使用普通 LLM Node，不强行 Agent 化。

------------------------------------------------------------------------

# 第二十七部分：Visual Agent

## Step 41：视觉规划

Visual Agent：

``` text
分析内容
 ↓
判断哪些位置需要视觉素材
 ↓
判断素材类型
 ↓
选择 Tool
```

Tools：

``` text
Image Search
Image Generation
Chart
```

例如：

-   真实人物/产品 → Search
-   概念场景 → Image Generation
-   数据趋势 → Chart

Visual Agent 属于 V2，可在时间不足时延期。

------------------------------------------------------------------------

# 第二十八部分：数据库

## Step 42：SQLite

保存：

``` text
Project
├── id
├── topic
├── plan
├── research
├── draft
├── review
├── final
├── status
└── created_at
```

可扩展：

-   Prompt Version
-   Token Usage
-   Rewrite Count
-   Error Log

------------------------------------------------------------------------

# 第二十九部分：异常处理

## Step 43：主动设计失败场景

至少处理：

-   API Key 错误
-   LLM Timeout
-   Search Timeout
-   Invalid JSON
-   RAG 无结果
-   Agent 超过最大次数
-   Rewrite 无限循环
-   空输入
-   超长输入
-   数据库异常

------------------------------------------------------------------------

# 第三十部分：测试计划

## Step 44：测试策略

覆盖：

### 功能测试

验证每个功能。

### 接口测试

验证 LLM / Search API。

### 异常测试

模拟 Timeout / 401 / 500 / Invalid JSON。

### 边界测试

空输入、超长文本等。

### Workflow 测试

验证不同 Router 路径。

### 回归测试

增加新功能后重新测试核心流程。

------------------------------------------------------------------------

# 第三十一部分：测试用例

## Step 45：建立 tests

示例：

``` text
TC01 正常主题
TC02 空主题
TC03 超长主题
TC04 LLM Timeout
TC05 Invalid JSON
TC06 Review < 80
TC07 Research 路由
TC08 Search 失败
TC09 Rewrite 达到上限
TC10 数据库存储
```

测试必须能追溯到 PRD 的验收标准。

------------------------------------------------------------------------

# 第三十二部分：Debug

## Step 46：按数据链路排查

``` text
UI
 ↓
Input
 ↓
Node
 ↓
Prompt
 ↓
LLM
 ↓
Parser
 ↓
State
 ↓
Router
 ↓
Tool
 ↓
Database
```

增加日志：

``` text
Node Start
Node End
Tool Call
Router Decision
Retry
Error
```

每个重要 Bug 记录：

``` text
现象
复现步骤
原因
定位过程
解决方案
回归结果
```

------------------------------------------------------------------------

# 第三十三部分：性能与成本

## Step 47：记录 AI 调用

观察：

-   每次任务 LLM 调用次数
-   Agent Tool Calls
-   Token Usage
-   总耗时
-   Rewrite 次数

优化：

-   减少无意义重复调用
-   限制 Agent Loop
-   控制 Context 长度
-   缓存可复用结果

------------------------------------------------------------------------

# 第三十四部分：安全与可靠性

## Step 48：基础安全

至少做到：

-   API Key 不入库/不提交 Git
-   用户输入基础校验
-   Tool 参数校验
-   文件路径安全
-   Agent 最大执行次数
-   明确 AI 输出可能存在错误
-   Research 内容保留来源

------------------------------------------------------------------------

# 第三十五部分：Git 工作流

## Step 49：持续 Commit

建议：

``` text
main
├── feature/planner
├── feature/writer
├── feature/reviewer
├── feature/langgraph
├── feature/research-agent
├── feature/rag
└── feature/visual-agent
```

Commit：

``` text
feat: add content planner
feat: implement reviewer schema
feat: migrate workflow to langgraph
feat: add research tool calling
fix: handle invalid llm output
fix: prevent infinite review loop
test: add workflow routing tests
docs: update architecture
```

------------------------------------------------------------------------

# 第三十六部分：代码 Review

## Step 50：每个模块完成后 Review

检查：

-   函数是否过长
-   模块职责是否单一
-   Prompt 是否与代码解耦
-   是否存在重复逻辑
-   错误是否被吞掉
-   API Key 是否安全
-   是否有测试
-   命名是否清晰

Codex / Claude Code 可以辅助 Review，但最终判断由开发者完成。

------------------------------------------------------------------------

# 第三十七部分：部署

## Step 51：部署前检查

确保：

-   requirements 完整
-   `.env.example`
-   启动命令
-   数据目录
-   错误提示
-   README

部署目标以"别人能够运行并体验"为准。

------------------------------------------------------------------------

# 第三十八部分：README

## Step 52：GitHub README

至少包含：

``` text
项目简介
解决的问题
功能
Demo
系统架构
Workflow
技术栈
项目结构
安装方式
配置方式
运行方式
测试
已知限制
Roadmap
```

不要只写安装命令。

------------------------------------------------------------------------

# 第三十九部分：项目 Demo

## Step 53：设计 Demo，而不是临时操作

建议：

``` text
1. 30秒：问题与项目目标
2. 30秒：系统架构
3. 2～3分钟：完整使用流程
4. 30秒：Research / Review / Router 展示
5. 30秒：技术亮点
6. 30秒：问题与优化
```

Demo 要展示 Workflow 的过程，而不仅是最终文章。

------------------------------------------------------------------------

# 第四十部分：项目报告

## Step 54：整理文档

项目报告可以从整个开发过程中积累的 docs 直接整理：

``` text
项目背景
需求分析
总体设计
技术选型
系统架构
核心实现
Agent
RAG
测试
问题与解决
运行结果
总结
```

因此不要第四周才开始补文档。

------------------------------------------------------------------------

# 第四十一部分：项目复盘

## Step 55：完成 Postmortem

回答：

1.  最初目标是什么？
2.  最终完成了什么？
3.  哪些功能被砍掉？
4.  最大技术问题是什么？
5.  最大产品问题是什么？
6.  哪个技术选型最有效？
7.  哪个设计可以改进？
8.  如果再给两周会做什么？

输出：

`docs/99-postmortem.md`

------------------------------------------------------------------------

# 第四十二部分：学习复盘

## Step 56：每个核心模块写 Learning Note

目录：

``` text
docs/learning-notes/
├── 01-requirement.md
├── 02-api-json.md
├── 03-prompt.md
├── 04-structured-output.md
├── 05-langgraph.md
├── 06-agent-tool-calling.md
├── 07-rag.md
├── 08-testing.md
└── 09-deployment.md
```

每篇回答：

1.  它是什么？
2.  为什么项目需要它？
3.  如何实现？
4.  遇到什么问题？
5.  如何解决？
6.  有什么局限？

------------------------------------------------------------------------

# 第四十三部分：简历

## Step 57：从事实生成项目描述

不要提前编造指标。

简历按照：

``` text
项目目标
+
技术架构
+
本人实现
+
关键问题
+
可验证结果
```

最终技术栈可类似：

> Python / Streamlit / LangGraph / LLM API / Pydantic / RAG / FAISS /
> SQLite

只有真正实现过的技术才能写。

------------------------------------------------------------------------

# 第四十四部分：面试准备

## Step 58：准备项目问题

必须能够回答：

-   为什么做这个项目？
-   为什么不是普通聊天机器人？
-   为什么用 LangGraph？
-   为什么 Writer 不是 Agent？
-   Research Agent 怎么工作？
-   Agent 和 Workflow 有什么区别？
-   Tool Calling 怎么实现？
-   RAG 为什么需要？
-   Chunk Size 怎么选？
-   Reviewer 怎么评价？
-   如何避免无限循环？
-   LLM 返回错误 JSON 怎么处理？
-   API Timeout 怎么处理？
-   项目遇到最大的 Bug 是什么？
-   为什么用 SQLite？
-   如果并发用户增加怎么办？
-   如果重新设计会改什么？

回答结构：

> 背景 → 问题 → 方案 → 实现 → Bug/权衡 → 结果 → 优化

------------------------------------------------------------------------

# 第四十五部分：四周项目计划

## Week 1 ------ 产品 + 基础工程

目标：

``` text
立项
需求分析
用户场景
竞品
PRD
MVP
User Flow
原型
验收标准
技术需求
技术选型
架构
Git
环境
LLM API
Planner
```

这一周重点不是赶代码，而是理解：

> 为什么做、给谁做、做什么、怎么判断做对了。

## Week 2 ------ MVP + AI 基础

完成：

``` text
Planner
Writer
Reviewer
Rewrite
Prompt Engineering
Structured Output
Pydantic
Streamlit MVP
```

得到第一个完整可运行版本。

## Week 3 ------ AI 工程化

完成：

``` text
LangGraph
State
Conditional Routing
Research Agent
Tool Calling
RAG
Quality Loop
```

重点理解：

> 为什么从普通 LLM App 演化成 Workflow / Agent 系统。

## Week 4 ------ 产品化与交付

完成：

``` text
Adapter
Visual Agent（时间允许）
SQLite
异常处理
测试
回归
Debug
性能/成本检查
部署
README
Demo
项目报告
复盘
简历
答辩准备
```

------------------------------------------------------------------------

# 第四十六部分：版本边界

## MVP

``` text
Topic
 ↓
Planner
 ↓
Writer
 ↓
Reviewer
 ↓
Rewrite
 ↓
Final
```

## V1 ------ 推荐课程最终版 / 简历版

``` text
USER
 ↓
Planner Node
 ↓
Research Agent
 ↓
Writer Node
 ↓
Reviewer Node
 ↓
Quality Router
 ↙          ↘
Research    Rewrite
 ↘          ↙
   Reviewer
      ↓
 Adapter Node
      ↓
    OUTPUT
```

包含：

-   LangGraph
-   Research Agent
-   Tool Calling
-   Structured Output
-   RAG
-   Streamlit
-   SQLite
-   Testing

## V2

增加：

``` text
Visual Agent
Image Search
Image Generation
PPT Generation
Storyboard
TTS
FFmpeg Video
```

V2 永远不能阻塞 V1 交付。

------------------------------------------------------------------------

# 第四十七部分：项目完成 Definition of Done

只有同时满足以下条件才视为完成：

-   项目问题定义清晰
-   目标用户明确
-   有需求分析
-   有用户场景
-   有 PRD
-   有 MVP 定义
-   有 User Flow
-   有原型
-   有验收标准
-   有技术选型依据
-   有架构图
-   有 Git 历史
-   有可运行系统
-   有 Structured Output
-   有 Workflow
-   至少一个真正 Tool-Using Agent
-   有 RAG 或明确说明为何未加入
-   有异常处理
-   有测试用例
-   有回归测试
-   有真实 Bug 记录
-   有 README
-   有运行说明
-   有 Demo
-   有项目报告
-   有复盘
-   能独立解释关键代码
-   能解释技术取舍
-   能讲出项目不足
-   简历内容与真实实现一致

------------------------------------------------------------------------

# 第四十八部分：AI 辅助开发规则

当使用本 Skill 的 AI 协助开发时：

## 禁止默认行为

不要：

-   一次性生成整个项目
-   跳过需求直接写代码
-   为了"高级"强行增加 Agent
-   为了简历强行增加 RAG
-   没有运行就进入下一阶段
-   用户不理解代码就继续堆功能

## 正确行为

每次只推进一个可验证阶段：

``` text
定位当前阶段
 ↓
说明目标
 ↓
解释必要知识
 ↓
设计输入输出
 ↓
实现最小版本
 ↓
运行验证
 ↓
Debug
 ↓
测试
 ↓
学习总结
 ↓
Git Commit
 ↓
下一阶段
```

如果用户说"继续"，先检查上一阶段是否真正完成。

------------------------------------------------------------------------

# 第四十九部分：最终学习目标

完成项目后，开发者不只是能够说：

> 我使用过 LangGraph、RAG 和 Agent。

而应该能够完整解释：

``` text
用户为什么需要这个产品
 ↓
需求如何变成功能
 ↓
功能如何变成技术需求
 ↓
为什么选择这些技术
 ↓
如何设计架构
 ↓
如何实现
 ↓
出现了哪些 Bug
 ↓
如何测试
 ↓
如何优化
 ↓
如何交付
 ↓
项目还有什么不足
```

这才是本 Skill 的最终目标：

> **通过 ContentFlow AI 完整学习一次 AI 应用从 0 到 1 的项目生命周期。**

最终开发思维：

**Problem → Requirement → Design → Architecture → Implementation → Test
→ Delivery → Reflection**
