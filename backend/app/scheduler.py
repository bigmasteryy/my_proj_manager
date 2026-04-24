from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from app.db.session import init_database


def scan_project_reminders() -> None:
    # Placeholder job. In the next step we can replace this with database scanning
    # for临期、逾期和高风险事项，然后写入 reminders 表。
    print(f"[{datetime.now().isoformat()}] scheduler heartbeat: scan reminders")


def main() -> None:
    init_database()
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(
        scan_project_reminders,
        trigger="interval",
        minutes=30,
        id="scan-project-reminders",
        replace_existing=True,
    )
    print("scheduler started")
    scheduler.start()


if __name__ == "__main__":
    main()
