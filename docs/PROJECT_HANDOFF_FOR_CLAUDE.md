# 项目交接文档（面向 Claude Code）

## 1. 文档目标

这份文档用于把当前项目移交到另一台机器，并让 Claude Code 在缺少口头背景的情况下，仍然能快速理解：

- 项目解决什么问题
- 代码当前实现到什么程度
- 前后端如何组织
- 数据模型是什么
- 哪些地方适合继续扩展
- 接手时有哪些实际风险

## 2. 项目概述

### 2.1 业务目标

该项目是一个“券商项目管理平台”原型/内部管理系统，围绕以下几类业务展开：

- 项目管理：维护券商项目、任务、风险、日志
- 进度推进：面向批量推进类项目，维护模板、实例、进度项、里程碑和风险
- 券商管理：维护券商基础信息、服务器、委托主站、版本信息、问题跟踪
- 个人工作台：维护个人每日任务、长期任务、个人风险、个人报告
- 通用管理：提醒、模板、报表、用户管理、系统页

### 2.2 当前阶段判断

从代码实现看，项目已经超过“纯静态原型”阶段，进入了“可本地运行、带 seed 数据的可演示业务系统”阶段，特征如下：

- 前后端联通
- 有登录和角色控制
- 有完整的前端路由和后台接口分域
- 有 SQLAlchemy 数据模型与 SQLite 持久化
- 有大量演示数据和默认账号
- 仍以 seed 数据驱动页面展示为主，离正式生产化仍有距离

## 3. 技术架构

### 3.1 技术栈

- 前端：
  - Vue 3
  - TypeScript
  - Vite
  - Vue Router
  - Element Plus
  - Axios
- 后端：
  - FastAPI
  - SQLAlchemy 2.x
  - Pydantic Settings
  - APScheduler
- 数据库：
  - SQLite
- 运行：
  - 本地 Python + npm
  - Docker Compose

### 3.2 目录结构

```text
proj-manager/
├─ backend/                  后端服务
│  ├─ app/
│  │  ├─ api/v1/             API 聚合路由
│  │  ├─ core/               配置
│  │  ├─ db/                 模型、会话、seed
│  │  └─ modules/            业务模块
│  ├─ data/                  Docker / 本地数据库文件目录
│  └─ requirements.txt
├─ frontend/                 前端应用
│  ├─ src/api/               按业务域拆分的接口层
│  ├─ src/views/             页面视图
│  ├─ src/router/            前端路由
│  ├─ src/layouts/           布局
│  └─ src/types/             前端类型
├─ docs/                     需求和交接文档
├─ prototype/                静态原型
├─ scripts/                  启动辅助脚本
├─ docker-compose.yml
└─ CLAUDE.md
```

## 4. 运行方式

### 4.1 本地开发

前端：

```powershell
cd frontend
npm install
npm run dev
```

后端：

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

地址：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`

### 4.2 一键启动脚本

仓库包含一个 Windows 友好的启动脚本：

- `scripts/start-services.ps1`

作用：

- 检测 8000/5173 端口是否已占用
- 自动启动后端和前端
- 检查 HTTP 是否就绪
- 输出本机地址和局域网地址

### 4.3 Docker Compose

```powershell
docker compose up --build
```

容器：

- `backend`
- `scheduler`
- `frontend`

Compose 下数据库通过环境变量固定为：

- `sqlite:///./data/broker_pm_local.db`

## 5. 后端架构说明

### 5.1 启动流程

入口文件：`backend/app/main.py`

关键行为：

- 创建 FastAPI 应用
- 挂载 CORS
- 注册 `api_router`
- 在 lifespan 中执行 `init_database()`

这意味着只要启动后端，数据库初始化和 seed 会自动触发。

### 5.2 配置

配置文件入口：`backend/app/core/config.py`

关键配置：

- `project_name`
- `api_prefix=/api/v1`
- `allowed_origins`
- `database_url`

本地默认数据库地址依赖：

- `%LOCALAPPDATA%/BrokerProjectManager/broker_pm_local.db`

这个设计规避了某些工作区目录对 SQLite 写入不稳定的问题。

### 5.3 数据层

核心文件：

- `backend/app/db/models.py`
- `backend/app/db/session.py`
- `backend/app/db/seed.py`

当前数据层特点：

- SQLAlchemy declarative 模型
- `Base.metadata.create_all()` 直接建表
- 没有完整的 Alembic 迁移链路
- 对 SQLite 历史字段兼容采用手写 `ALTER TABLE` 的方式

这套方式适合原型和演示，不适合中长期复杂生产迭代。若后续继续深做，建议优先建立正式迁移。

### 5.4 模块划分

后端业务模块位于 `backend/app/modules/`：

- `auth`：登录、当前用户、登出、权限依赖
- `brokers`：券商基础信息、资产、版本等
- `broker_issues`：券商问题跟踪
- `dashboard`：首页汇总
- `logs`：历史与日志
- `personal`：个人任务/个人视角
- `progress`：推进模板、推进实例、进展、风险
- `projects`：项目列表、项目详情
- `reminders`：提醒
- `reports`：报表
- `risks`：风险中心
- `system`：系统页
- `tasks`：任务
- `templates`：模板中心
- `users`：用户管理

### 5.5 权限模型

后端 API 聚合在 `backend/app/api/v1/router.py`。

权限分两层：

- `get_current_user`
- `require_admin`

实际效果：

- 登录、登出、当前用户接口属于通用入口
- 管理类业务页面大多要求 `admin`
- 个人相关页面允许普通用户访问

### 5.6 认证机制

认证逻辑在 `backend/app/modules/auth/`。

当前方案：

- 用户密码通过 PBKDF2-SHA256 存储
- 登录后创建 `UserSession`
- 使用 Bearer Token
- Session 默认有效期 30 天

默认 seed 账号：

- 管理员：`admin / admin123`
- 普通用户：`user01 / user123`

## 6. 核心数据模型

以下是最重要的业务实体，便于 Claude Code 快速建立领域概念。

### 6.1 券商域

- `Broker`
  - 券商基础信息
  - 含业务状态、系统版本、是否精选等字段
- `BrokerServer`
  - 券商服务器资产
- `BrokerEntrustSite`
  - 券商委托主站 / 客户端站点信息
- `BrokerIssue`
  - 问题/需求主记录
- `BrokerIssueStatus`
  - 某个问题在不同券商上的影响与修复状态

### 6.2 项目域

- `Project`
  - 单个项目主记录
- `Task`
  - 项目任务
- `Risk`
  - 项目风险
- `ProjectLog`
  - 项目日志

### 6.3 推进域

推进域是当前项目比较有特色的一块。

- `ProgressProjectTemplate`
  - 推进模板，例如本地路由升级、Linux 主站推进、信创推进
- `ProgressItemTemplate`
  - 模板下的推进项
- `ProgressBrokerProjectInstance`
  - 某券商的某推进项目实例
- `ProgressItemValue`
  - 实例下各推进项的实际值
- `ProgressLog`
  - 推进日志
- `ProgressRisk`
  - 推进风险
- `ProgressStage2GroupTemplate`
  - 第二阶段分组模板
- `ProgressStage2StepTemplate`
  - 第二阶段步骤模板
- `ProgressStage2StepInstance`
  - 第二阶段步骤实例

从模型看，系统已经不仅是“项目列表”，而是在做一套“批量推进项目模板化管理”的能力。

### 6.4 个人任务域

- `PersonalTask`
  - 支持每日任务 / 长期任务
  - 支持父子任务结构
  - 支持完成结果、排序

### 6.5 通用域

- `Reminder`
- `Template`
- `TemplateTask`
- `TemplateRisk`
- `User`
- `UserSession`

## 7. Seed 数据策略

### 7.1 作用

`backend/app/db/seed.py` 不是简单示例，而是当前系统可演示性的关键组成部分。

它会初始化：

- 用户账号
- 券商基础数据
- 服务器与委托主站数据
- 券商问题数据
- 项目、任务、风险、日志
- 推进模板和推进实例
- 个人任务

### 7.2 影响

很多页面是否“有真实内容”取决于 seed。

因此后续开发时要注意：

- 如果新增页面却没有 seed，页面可能看起来像“功能坏了”
- 如果修改模型但不调整 seed，初始化可能失败或页面字段为空

### 7.3 重置策略

`backend/app/db/session.py` 里有：

- `init_database()`
- `reset_demo_database()`

这说明当前系统天然支持“重建演示库”的工作流。

## 8. 前端架构说明

### 8.1 总体结构

前端入口是一个典型的 Vue 3 单页应用：

- 路由：`frontend/src/router/index.ts`
- 布局：`frontend/src/layouts/AppLayout.vue`
- 接口封装：`frontend/src/api/*.ts`
- 页面：`frontend/src/views/*`
- 类型：`frontend/src/types/models.ts`

### 8.2 接口层

`frontend/src/api/client.ts` 提供统一的 axios 实例：

- `baseURL=/api/v1`
- 请求自动注入 token
- `401` 自动清 session 并跳转登录页
- `unwrap()` 用于提取统一响应体的 `data`

这说明前端假定后端返回结构是统一的 `ApiResponse<T>`。

### 8.3 路由与页面分区

路由定义在 `frontend/src/router/index.ts`，当前已覆盖这些页面组：

- 登录
- 管理驾驶舱
- 项目推进总览 / 矩阵 / 券商视角 / 风险 / 报告 / 实例详情
- 新券商接入
- 券商台账 / 服务器 / 委托主站 / 版本 / 问题
- 项目列表 / 项目详情
- 风险中心
- 个人每日 / 长期 / 风险 / 报告
- 个人与项目历史
- 用户管理
- 模板中心
- 工作日历
- 报表

从路由可以看出，前端已经具备比较完整的信息架构。

### 8.4 权限前端侧处理

前端在路由守卫中判断：

- 是否登录
- 是否 `admin`

普通用户访问管理员页面会被重定向到个人首页。

## 9. 当前已实现能力总结

基于代码结构，当前系统至少已经实现或具备可演示雏形的能力包括：

- 登录与会话管理
- 管理员 / 普通用户角色切分
- 项目列表与项目详情展示
- 风险、日志、提醒、模板、报表的基础展示
- 券商台账与券商扩展信息管理
- 券商问题跟踪
- 批量推进项目模板、实例、推进项、里程碑、风险
- 个人任务管理
- Docker / 本地双运行方式

## 10. 当前代码状态风险

### 10.1 迁移机制不正式

当前数据库变更通过：

- `create_all()`
- 手写 SQLite 兼容 `ALTER TABLE`

短期可用，长期会变成维护负担。

### 10.2 seed 体量较大

`seed.py` 已经承担了：

- 演示数据
- 默认账号
- 页面“是否可用”的支撑

这意味着：

- seed 变更有较强副作用
- 后续应考虑拆分为领域 seed、测试 seed、演示 seed

### 10.3 当前工作区可能存在未提交改动

在生成本交接文档时，工作区存在本地未提交文件，涉及：

- 券商管理
- 券商问题
- 推进视图
- 总览页面
- 新券商接入

这对跨机器移交非常重要：

- 如果另一台机器只 clone 远端仓库，这些本地改动不会自动带过去
- 移交前应先确认是否需要提交这些改动，或者直接复制完整工作目录

### 10.4 文本编码历史问题

部分中文在某些终端读取时可能出现乱码，说明当前项目在“文件本身编码”和“终端显示编码”之间存在历史差异。

建议：

- 统一使用 UTF-8
- 在 Windows PowerShell 中确认终端编码
- 后续编辑尽量避免混合编码

## 11. Claude Code 接手后的推荐工作流

### 11.1 第一步：建立运行验证

建议 Claude Code 接手后的第一轮操作顺序：

1. 阅读 `CLAUDE.md`
2. 阅读本交接文档
3. 启动后端并确认 `/docs`
4. 启动前端并确认能登录
5. 用 `admin/admin123` 走一遍主菜单
6. 用 `user01/user123` 走一遍个人菜单

### 11.2 第二步：建立模块边界感

新增功能时优先保持现有边界：

- 后端：`app/modules/<domain>/router.py + schemas.py`
- 前端：`src/api/<domain>.ts + src/views/<domain>/`

不要把临时逻辑堆进：

- 单个大 router
- 单个大 view
- 单个公共 util 文件

### 11.3 第三步：优先补工程化短板

如果目标是继续长期维护，优先顺序建议是：

1. 梳理未提交改动并入库
2. 统一编码与基础文档
3. 引入正式迁移机制
4. 增加最基础的接口测试/页面冒烟测试
5. 明确哪些数据是演示数据，哪些是正式业务数据

## 12. 后续开发建议

### 12.1 适合优先推进的方向

- 项目、任务、风险、提醒的增删改查闭环
- 推进实例编辑体验完善
- 券商资产与版本联动能力
- 报表导出能力
- 用户与权限体系补强

### 12.2 如果要迈向生产

建议补齐这些能力：

- PostgreSQL 替代 SQLite
- Alembic 正式迁移
- 接口测试
- 前端构建/发布文档
- 配置分环境
- 日志与审计
- 更细粒度权限模型

## 13. 建议的阅读顺序

如果 Claude Code 要开始做功能开发，推荐按以下顺序读代码：

1. `backend/app/main.py`
2. `backend/app/api/v1/router.py`
3. `backend/app/db/models.py`
4. `backend/app/db/session.py`
5. `backend/app/db/seed.py`
6. `frontend/src/router/index.ts`
7. `frontend/src/api/client.ts`
8. 对应业务域的 `router.py / schemas.py / view.vue / api.ts`

## 14. 交接结论

该项目当前已经具备：

- 可运行
- 可登录
- 可演示
- 模块化边界清晰

但仍属于“内部管理系统原型向可持续工程化系统过渡”的阶段。

对于 Claude Code 来说，这个仓库是可继续维护和扩展的，前提是先处理两件事：

- 确认本地未提交改动是否需要一起移交
- 逐步把 seed 驱动原型提升为可迁移、可测试、可持续迭代的工程结构

