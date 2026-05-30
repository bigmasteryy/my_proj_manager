from __future__ import annotations

import unittest
from datetime import date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import (
    Broker,
    BrokerIssue,
    BrokerIssueStatus,
    ProgressBrokerProjectInstance,
    ProgressProjectTemplate,
)
from app.db.session import Base
from app.modules.progress.router import get_broker_progress_projects


class BrokerProgressViewTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
        Base.metadata.create_all(engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)

    def test_broker_progress_view_includes_related_issues_and_requirements(self) -> None:
        now = datetime(2026, 5, 26, 9, 30)
        with self.SessionLocal() as session:
            broker = Broker(
                name="华东证券",
                short_name="华东",
                status="active",
                business_status="运行中",
            )
            other_broker = Broker(
                name="华南证券",
                short_name="华南",
                status="active",
                business_status="运行中",
            )
            template = ProgressProjectTemplate(
                code="linux-main-site",
                name="Linux 主站推进",
                project_type="重点推进",
                description="",
                status="active",
                sort_no=1,
                created_at=now,
                updated_at=now,
            )
            session.add_all([broker, other_broker, template])
            session.flush()

            session.add(
                ProgressBrokerProjectInstance(
                    project_template_id=template.id,
                    broker_id=broker.id,
                    input_mode="明细",
                    overall_status="推进中",
                    progress_percent=50,
                    latest_update_at=now,
                    risk_count=0,
                    milestone_count=1,
                    created_at=now,
                    updated_at=now,
                )
            )
            issue = BrokerIssue(
                issue_type="新需求",
                title="柜台批量升级确认",
                priority="高",
                status="开发中",
                description="",
                impact_scope="影响 Linux 主站上线窗口",
                planned_fix_version="V2.4.1",
                solution="",
                owner_name="张三",
                planned_finish_date=date(2026, 5, 30),
                remark="",
                created_at=now,
                updated_at=now,
            )
            unrelated_issue = BrokerIssue(
                issue_type="线上问题",
                title="其他券商问题",
                priority="中",
                status="待分析",
                created_at=now,
                updated_at=now,
            )
            session.add_all([issue, unrelated_issue])
            session.flush()
            session.add_all(
                [
                    BrokerIssueStatus(
                        issue_id=issue.id,
                        broker_id=broker.id,
                        is_affected=True,
                        impact_desc="需和推进计划一起跟踪",
                        fix_status="修复中",
                        fix_version="V2.4.1",
                        owner_name="李四",
                        updated_at=now,
                    ),
                    BrokerIssueStatus(
                        issue_id=unrelated_issue.id,
                        broker_id=other_broker.id,
                        is_affected=True,
                        fix_status="未开始",
                        updated_at=now,
                    ),
                ]
            )
            session.commit()

            result = get_broker_progress_projects(broker.id, session)

        data = result["data"]
        self.assertEqual("华东证券", data["brokerName"])
        self.assertEqual(1, len(data["projects"]))
        self.assertEqual(1, len(data["issues"]))
        self.assertEqual(
            {
                "id": issue.id,
                "issueType": "新需求",
                "title": "柜台批量升级确认",
                "priority": "高",
                "status": "开发中",
                "fixStatus": "修复中",
                "impactDesc": "需和推进计划一起跟踪",
                "plannedFixVersion": "V2.4.1",
                "plannedFinishDate": "2026-05-30",
                "ownerName": "李四",
                "updatedAt": "2026-05-26",
            },
            data["issues"][0],
        )


if __name__ == "__main__":
    unittest.main()
