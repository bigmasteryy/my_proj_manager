# A/B 机器部署与自动同步方案

## 1. 目标

当前协作方式：

- A 机器负责主要开发，并推送到 GitHub。
- B 机器负责部署运行。
- B 机器偶尔也需要开发。
- A 机器推送后，B 机器能够自动拉取更新，并重建/重启服务。

推荐方案：B 机器主动定时拉取 GitHub。这样不要求 B 机器有公网 IP，也不要求 GitHub 能访问 B 机器。

## 2. 核心原则

B 机器必须分成两个目录：

- 部署目录：只用于自动更新和运行服务，例如 `D:\apps\proj-manager-deploy`
- 开发目录：只用于 B 机器临时开发，例如 `D:\work\proj-manager-dev`

不要在部署目录里直接改代码。自动更新脚本会检查本地是否有改动，如果发现部署目录不干净，会停止更新，避免覆盖 B 机器上的开发内容。

## 3. B 机器首次部署

### 3.1 安装依赖

B 机器需要安装：

- Git
- Docker Desktop 或 Docker Engine
- PowerShell
- GitHub SSH key 或 HTTPS 凭据

确认命令可用：

```powershell
git --version
docker --version
docker compose version
```

### 3.2 克隆部署目录

```powershell
mkdir D:\apps
git clone git@github.com:bigmasteryy/my_proj_manager.git D:\apps\proj-manager-deploy
cd D:\apps\proj-manager-deploy
```

如果 B 机器尚未配置 SSH，也可以先用 HTTPS：

```powershell
git clone https://github.com/bigmasteryy/my_proj_manager.git D:\apps\proj-manager-deploy
```

### 3.3 首次启动服务

```powershell
cd D:\apps\proj-manager-deploy
docker compose up -d --build
```

访问地址：

- 前端：`http://127.0.0.1:5173`
- 后端 Swagger：`http://127.0.0.1:8000/docs`

默认账号：

- 管理员：`admin / admin123`
- 普通用户：`user01 / user123`

## 4. 配置 B 机器自动更新

仓库内置自动更新脚本：

- `scripts/deploy/update-from-github.ps1`

手动执行一次：

```powershell
cd D:\apps\proj-manager-deploy
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy\update-from-github.ps1
```

安装 Windows 计划任务，每 5 分钟检查一次 GitHub：

```powershell
cd D:\apps\proj-manager-deploy
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy\install-auto-update-task.ps1 -IntervalMinutes 5
```

立即触发一次：

```powershell
schtasks /Run /TN BrokerProjectManagerAutoUpdate
```

查看日志：

```powershell
Get-Content $env:LOCALAPPDATA\BrokerProjectManager\auto-update.log -Tail 80
```

## 5. 自动更新脚本做了什么

每次运行时，脚本会：

1. 确认当前目录是 Git 仓库。
2. 确认当前分支是 `main`。
3. 确认部署目录没有本地改动。
4. 执行 `git fetch origin main`。
5. 如果远端有新提交，执行 `git merge --ff-only origin/main`。
6. 执行 `docker compose up -d --build --remove-orphans`。
7. 检查后端 `http://127.0.0.1:8000/docs`。
8. 检查前端 `http://127.0.0.1:5173`。

如果没有新提交，默认不重建服务。

强制重建：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy\update-from-github.ps1 -ForceBuild
```

## 6. B 机器也要开发时怎么做

在 B 机器另建开发目录：

```powershell
mkdir D:\work
git clone git@github.com:bigmasteryy/my_proj_manager.git D:\work\proj-manager-dev
cd D:\work\proj-manager-dev
git switch -c feature/some-change
```

B 机器开发完成后：

```powershell
git add .
git commit -m "feat: describe the change"
git push origin feature/some-change
```

合并到 `main` 后，部署目录会在下一次自动更新时拉取并重启服务。

## 7. A 机器日常开发流程

A 机器正常开发：

```powershell
git status
git add .
git commit -m "feat: describe the change"
git push origin main
```

B 机器自动更新任务会在下一个周期检测到 `main` 的新提交并更新服务。

## 8. 常见问题

### 8.1 自动更新失败：部署目录有本地改动

原因：有人在 `D:\apps\proj-manager-deploy` 里改了代码。

处理：

```powershell
cd D:\apps\proj-manager-deploy
git status
```

如果这些改动需要保留，转移到开发目录后提交。部署目录应保持干净。

### 8.2 自动更新失败：不是 main 分支

原因：部署目录被切到了其他分支。

处理：

```powershell
cd D:\apps\proj-manager-deploy
git switch main
```

### 8.3 服务没有起来

查看容器：

```powershell
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
```

手动重建：

```powershell
docker compose up -d --build --remove-orphans
```

## 9. 可选增强

如果 B 机器有公网 IP，或者可以被 GitHub Actions 通过 SSH 访问，可以进一步改为：

- GitHub Actions 在 `main` 更新后 SSH 到 B 机器执行部署脚本。

但当前推荐保留 B 机器主动拉取模式，因为它对网络环境要求最低，也更适合内网机器。

