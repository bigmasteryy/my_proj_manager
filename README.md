# 项目管理平台

基于 `Vue 3 + TypeScript + FastAPI + SQLite + Docker Compose` 的项目管理平台工程骨架。

## 当前已落地内容

- `docs/`：需求文档与 PRD
- `prototype/`：高保真静态原型
- `frontend/`：Vue 3 + TypeScript + Element Plus 页面骨架
- `backend/`：FastAPI 模块化 API 骨架
- `docker-compose.yml`：本地联调容器编排

## 数据库说明

当前默认使用本地 SQLite 文件数据库：

- 数据库文件：`%LOCALAPPDATA%/BrokerProjectManager/broker_pm_local.db`
- 默认连接串：运行本机 Python 时会自动指向上述本地目录

这样做的好处是：

1. 本地开发零依赖，不需要先装数据库服务
2. 单机使用和早期原型阶段更轻
3. 后续如果需要切到 PostgreSQL，再替换 `DATABASE_URL` 即可

## 本地开发

### 前端

```powershell
cd frontend
npm install
npm run dev
```

前端默认地址：

- `http://localhost:5173`

### 后端

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

首次启动时会自动初始化 SQLite 数据库目录。

说明：

- 本机直接运行 Python 时，默认把 SQLite 文件放到用户本地数据目录，避开某些工作区目录下的 SQLite 写入限制
- Docker Compose 里仍使用容器内的 `./data/broker_pm_local.db`

后端默认地址：

- `http://localhost:8000`
- Swagger 文档：`http://localhost:8000/docs`

### 调度服务

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m app.scheduler
```

## Docker Compose

```powershell
docker compose up --build
```

启动后默认服务：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- SQLite 文件：
  - 本机运行：`%LOCALAPPDATA%/BrokerProjectManager/broker_pm_local.db`
  - Docker Compose：`backend/data/broker_pm_local.db`

## 当前阶段说明

当前代码以工程骨架和示例数据联调为主，下一步建议继续补：

1. SQLAlchemy 模型与数据库真实落表
2. 项目、任务、风险、提醒的增删改查接口
3. 前端表单录入、新建/编辑弹窗
4. 提醒扫描规则落到数据库和调度服务
