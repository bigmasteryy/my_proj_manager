from fastapi import APIRouter
from fastapi import Depends

from app.modules.auth.deps import get_current_user, require_admin
from app.modules.auth.router import router as auth_router
from app.modules.brokers.router import router as brokers_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.logs.router import history_router as history_logs_router
from app.modules.logs.router import router as logs_router
from app.modules.personal.router import router as personal_router
from app.modules.progress.router import router as progress_router
from app.modules.projects.router import router as projects_router
from app.modules.reminders.router import router as reminders_router
from app.modules.reports.router import router as reports_router
from app.modules.risks.router import router as risks_router
from app.modules.system.router import router as system_router
from app.modules.tasks.router import router as tasks_router
from app.modules.templates.router import router as templates_router
from app.modules.users.router import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(dashboard_router, dependencies=[Depends(require_admin)])
api_router.include_router(brokers_router, dependencies=[Depends(require_admin)])
api_router.include_router(history_logs_router, dependencies=[Depends(require_admin)])
api_router.include_router(projects_router, dependencies=[Depends(require_admin)])
api_router.include_router(progress_router, dependencies=[Depends(require_admin)])
api_router.include_router(logs_router, dependencies=[Depends(require_admin)])
api_router.include_router(personal_router, dependencies=[Depends(get_current_user)])
api_router.include_router(tasks_router, dependencies=[Depends(require_admin)])
api_router.include_router(risks_router, dependencies=[Depends(require_admin)])
api_router.include_router(reminders_router, dependencies=[Depends(require_admin)])
api_router.include_router(templates_router, dependencies=[Depends(require_admin)])
api_router.include_router(reports_router, dependencies=[Depends(require_admin)])
api_router.include_router(system_router, dependencies=[Depends(require_admin)])
api_router.include_router(users_router)
