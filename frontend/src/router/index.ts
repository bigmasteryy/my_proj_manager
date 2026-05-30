import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import AppLayout from "../layouts/AppLayout.vue";
import { getStoredUser, isAuthenticated } from "../utils/auth";

const LoginView = () => import("../views/auth/LoginView.vue");
const DashboardView = () => import("../views/dashboard/DashboardView.vue");
const ProgressOverviewView = () => import("../views/progress/ProgressOverviewView.vue");
const ProgressMatrixView = () => import("../views/progress/ProgressMatrixView.vue");
const BrokerProgressView = () => import("../views/progress/BrokerProgressView.vue");
const ProgressLogsView = () => import("../views/progress/ProgressLogsView.vue");
const ProgressRisksView = () => import("../views/progress/ProgressRisksView.vue");
const ProgressReportView = () => import("../views/progress/ProgressReportView.vue");
const ProgressInstanceDetailView = () => import("../views/progress/ProgressInstanceDetailView.vue");
const NewBrokerOnboardingView = () => import("../views/newBroker/NewBrokerOnboardingView.vue");
const NewBrokerCreateView = () => import("../views/newBroker/NewBrokerCreateView.vue");
const WorkdayCalendarView = () => import("../views/newBroker/WorkdayCalendarView.vue");
const BrokerOverviewView = () => import("../views/overview/BrokerOverviewView.vue");
const BrokerLedgerView = () => import("../views/brokers/BrokerLedgerView.vue");
const BrokerServersView = () => import("../views/brokers/BrokerServersView.vue");
const BrokerEntrustSitesView = () => import("../views/brokers/BrokerEntrustSitesView.vue");
const BrokerVersionView = () => import("../views/brokers/BrokerVersionView.vue");
const BrokerIssuesView = () => import("../views/brokers/BrokerIssuesView.vue");
const ProjectListView = () => import("../views/project/ProjectListView.vue");
const ProjectDetailView = () => import("../views/project/ProjectDetailView.vue");
const RiskCenterView = () => import("../views/risks/RiskCenterView.vue");
const TemplateCenterView = () => import("../views/templates/TemplateCenterView.vue");
const ReportView = () => import("../views/reports/ReportView.vue");
const ProjectHistoryView = () => import("../views/history/ProjectHistoryView.vue");
const PersonalHistoryView = () => import("../views/history/PersonalHistoryView.vue");
const PersonalTasksView = () => import("../views/personal/PersonalTasksView.vue");
const LongTermTasksView = () => import("../views/personal/LongTermTasksView.vue");
const PersonalRiskView = () => import("../views/personal/PersonalRiskView.vue");
const PersonalReportView = () => import("../views/personal/PersonalReportView.vue");
const UserManagementView = () => import("../views/users/UserManagementView.vue");

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "login",
    component: LoginView
  },
  {
    path: "/",
    component: AppLayout,
    redirect: "/overview/projects",
    meta: { requiresAuth: true },
    children: [
      { path: "dashboard", name: "dashboard", component: DashboardView, meta: { requiresAdmin: true } },
      { path: "overview/projects", name: "overview-projects", component: ProgressOverviewView, meta: { requiresAdmin: true } },
      { path: "overview/brokers", name: "overview-brokers", component: BrokerOverviewView, meta: { requiresAdmin: true } },
      { path: "progress/overview", redirect: "/overview/projects" },
      { path: "progress/matrix", name: "progress-matrix", component: ProgressMatrixView, meta: { requiresAdmin: true } },
      { path: "progress/brokers", name: "progress-brokers", component: BrokerProgressView, meta: { requiresAdmin: true } },
      { path: "progress/logs", name: "progress-logs", component: ProgressLogsView, meta: { requiresAdmin: true } },
      { path: "progress/risks", name: "progress-risks", component: ProgressRisksView, meta: { requiresAdmin: true } },
      { path: "progress/reports", name: "progress-reports", component: ProgressReportView, meta: { requiresAdmin: true } },
      { path: "progress/instances/:id", name: "progress-instance-detail", component: ProgressInstanceDetailView, meta: { requiresAdmin: true } },
      { path: "new-brokers", name: "new-brokers", component: NewBrokerOnboardingView, meta: { requiresAdmin: true } },
      { path: "new-brokers/create", name: "new-broker-create", component: NewBrokerCreateView, meta: { requiresAdmin: true } },
      { path: "brokers", name: "brokers", component: BrokerLedgerView, meta: { requiresAdmin: true } },
      { path: "brokers/servers", name: "broker-servers", component: BrokerServersView, meta: { requiresAdmin: true } },
      { path: "brokers/entrust-sites", name: "broker-entrust-sites", component: BrokerEntrustSitesView, meta: { requiresAdmin: true } },
      { path: "brokers/versions", name: "broker-versions", component: BrokerVersionView, meta: { requiresAdmin: true } },
      { path: "brokers/issues", name: "broker-issues", component: BrokerIssuesView, meta: { requiresAdmin: true } },
      { path: "projects", name: "projects", component: ProjectListView, meta: { requiresAdmin: true } },
      { path: "projects/:id", name: "project-detail", component: ProjectDetailView, meta: { requiresAdmin: true } },
      { path: "risks", name: "risks", component: RiskCenterView, meta: { requiresAdmin: true } },
      { path: "personal", redirect: "/personal/daily" },
      { path: "personal/daily", name: "personal-daily", component: PersonalTasksView },
      { path: "personal/long-term", name: "personal-long-term", component: LongTermTasksView },
      { path: "personal/risks", name: "personal-risks", component: PersonalRiskView },
      { path: "personal/reports", name: "personal-reports", component: PersonalReportView },
      { path: "history", redirect: "/history/personal" },
      { path: "history/project", name: "project-history", component: ProjectHistoryView, meta: { requiresAdmin: true } },
      { path: "history/personal", name: "personal-history", component: PersonalHistoryView },
      { path: "users", name: "users", component: UserManagementView, meta: { requiresAdmin: true } },
      { path: "templates", name: "templates", component: TemplateCenterView, meta: { requiresAdmin: true } },
      { path: "workday-calendar", name: "workday-calendar", component: WorkdayCalendarView, meta: { requiresAdmin: true } },
      { path: "reports", name: "reports", component: ReportView, meta: { requiresAdmin: true } }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to) => {
  if (to.path === "/login") {
    if (isAuthenticated()) {
      const user = getStoredUser();
      return user?.role === "admin" ? "/overview/projects" : "/personal/daily";
    }
    return true;
  }

  if (to.matched.some((record) => record.meta.requiresAuth) && !isAuthenticated()) {
    return {
      path: "/login",
      query: {
        redirect: to.fullPath
      }
    };
  }

  if (to.matched.some((record) => record.meta.requiresAdmin)) {
    const user = getStoredUser();
    if (!user || user.role !== "admin") {
      return "/personal/daily";
    }
  }

  return true;
});

export default router;
