import { http, unwrap } from "./client";
import type {
  ProgressBrokerSimple,
  ProgressBrokerView,
  ProgressInstanceDetail,
  ProgressLogCreatePayload,
  ProgressLogItem,
  ProgressMatrixResponse,
  ProgressProjectSummary,
  ProgressRiskCreatePayload,
  ProgressRiskItem,
  ProgressRiskUpdatePayload,
  ProgressValueUpdatePayload,
  WeeklyReport
} from "../types/models";

export function getProgressProjects() {
  return unwrap<ProgressProjectSummary[]>(http.get("/progress/projects"));
}

export function getProgressMatrix(projectTemplateId: number) {
  return unwrap<ProgressMatrixResponse>(http.get(`/progress/projects/${projectTemplateId}/matrix`));
}

export function getProgressBrokers() {
  return unwrap<ProgressBrokerSimple[]>(http.get("/progress/brokers"));
}

export function getBrokerProgressProjects(brokerId: number) {
  return unwrap<ProgressBrokerView>(http.get(`/progress/brokers/${brokerId}/projects`));
}

export function getProgressInstanceDetail(instanceId: number) {
  return unwrap<ProgressInstanceDetail>(http.get(`/progress/instances/${instanceId}`));
}

export function getProgressLogs(params: {
  project_template_id?: number;
  broker_id?: number;
  instance_id?: number;
  keyword?: string;
  only_milestone?: boolean;
}) {
  return unwrap<ProgressLogItem[]>(http.get("/progress/logs", { params }));
}

export function getProgressRisks(params: {
  project_template_id?: number;
  broker_id?: number;
  status?: string;
}) {
  return unwrap<ProgressRiskItem[]>(http.get("/progress/risks", { params }));
}

export function getProgressWeeklyReport(projectTemplateId?: number) {
  return unwrap<WeeklyReport>(http.get("/progress/reports/weekly", { params: { project_template_id: projectTemplateId } }));
}

export function updateProgressItemValue(instanceId: number, itemTemplateId: number, payload: ProgressValueUpdatePayload) {
  return unwrap(http.post(`/progress/instances/${instanceId}/items/${itemTemplateId}/update`, payload));
}

export function createProgressLog(instanceId: number, payload: ProgressLogCreatePayload) {
  return unwrap(http.post(`/progress/instances/${instanceId}/logs`, payload));
}

export function createProgressRisk(instanceId: number, payload: ProgressRiskCreatePayload) {
  return unwrap(http.post(`/progress/instances/${instanceId}/risks`, payload));
}

export function updateProgressRisk(riskId: number, payload: ProgressRiskUpdatePayload) {
  return unwrap(http.put(`/progress/risks/${riskId}`, payload));
}
