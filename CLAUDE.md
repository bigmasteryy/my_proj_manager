# Claude Code Quick Handoff

本文件给接手维护该仓库的 Claude Code 使用，目标是在最短时间内建立项目全貌。

## 1. 项目定位

- 项目名称：券商项目管理平台 / Broker Project Manager
- 目标：统一管理券商项目、推进进度、风险、提醒、个人任务，以及券商侧资产与问题跟踪
- 技术栈：
  - 前端：Vue 3 + TypeScript + Vite + Element Plus + Vue Router + Axios
  - 后端：FastAPI + SQLAlchemy + SQLite + APScheduler
  - 运行方式：本地直接运行，或通过 Docker Compose 联调

## 2. 先看哪里

接手时优先阅读这些文件：

1. `docs/PROJECT_HANDOFF_FOR_CLAUDE.md`
2. `backend/app/main.py`
3. `backend/app/api/v1/router.py`
4. `backend/app/db/models.py`
5. `backend/app/db/session.py`
6. `frontend/src/router/index.ts`
7. `frontend/src/api/client.ts`
8. `scripts/start-services.ps1`

## 3. 本地启动

### 前端

```powershell
cd frontend
npm install
npm run dev
```

默认地址：

- `http://localhost:5173`

### 后端

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

默认地址：

- API：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`

### 一键启动脚本

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-services.ps1
```

## 4. 关键事实

- 后端启动时会自动：
  - 创建 SQLite 数据库目录
  - `create_all`
  - 执行内置 seed
- 默认数据库：
  - 本地 Python 运行：`%LOCALAPPDATA%/BrokerProjectManager/broker_pm_local.db`
  - Docker Compose：`backend/data/broker_pm_local.db`
- 默认演示账号：
  - 管理员：`admin / admin123`
  - 普通用户：`user01 / user123`
- 前端通过 `Authorization: Bearer <token>` 调后端
- 权限模型分两类：
  - `admin`：可访问后台管理、券商管理、项目推进、模板、报表等
  - `user`：主要访问个人任务、个人历史、个人风险与个人报告

## 5. 开发注意点

- 当前仓库后端没有使用 Alembic 正式迁移流程，SQLite 字段兼容逻辑写在 `backend/app/db/session.py` 的 `_apply_sqlite_compat_migrations()`
- 演示数据依赖 `backend/app/db/seed.py`，很多页面是否“有内容”取决于 seed 是否完整
- 前端页面和后端接口基本按业务域一一对应，新增功能时优先沿用已有模块边界，不要把接口和页面耦合到单个大文件里
- 当前工作区曾有未提交业务改动，跨机器移交时不要只依赖远端仓库，先确认本地改动是否已经提交

## 6. 维护策略建议

- 小改动优先保持现有模块边界：
  - 后端：`app/modules/<domain>/`
  - 前端：`src/api/<domain>.ts` + `src/views/<domain>/`
- 如果要扩展到真实生产环境：
  - 把 SQLite 切换到 PostgreSQL
  - 建立正式迁移脚本
  - 梳理 seed 与正式数据的边界
  - 补充鉴权、审计、测试和部署说明

