import { http, unwrap } from "./client";
import type {
  ProgressBrokerSimple,
  ProgressBrokerView,
  ProgressItemTemplateCreatePayload,
  ProgressInstanceDetail,
  ProgressLogCreatePayload,
  ProgressLogItem,
  ProgressMatrixAiAnalysis,
  ProgressMatrixResponse,
  ProgressFeaturedProjectsUpdatePayload,
  ProgressProjectOverview,
  ProgressProjectBrokerAddPayload,
  ProgressProjectCreatePayload,
  ProgressProjectSummary,
  ProgressRiskCreatePayload,
  ProgressRiskItem,
  ProgressRiskUpdatePayload,
  ProgressStage2StepCreatePayload,
  ProgressStage2StepMovePayload,
  ProgressStage2StepUpdatePayload,
  ProgressTaskCreatePayload,
  ProgressTaskStatusPayload,
  ProgressTaskUpdatePayload,
  ProgressValueUpdatePayload,
  WeeklyReport
} from "../types/models";

export function getProgressProjects() {
  return unwrap<ProgressProjectSummary[]>(http.get("/progress/projects"));
}

export function getProgressProjectOverview() {
  return unwrap<ProgressProjectOverview>(http.get("/progress/overview/projects"));
}

export function updateProgressFeaturedProjects(payload: ProgressFeaturedProjectsUpdatePayload) {
  return unwrap<{ projectTemplateIds: number[] }>(http.post("/progress/overview/projects/featured", payload));
}

export function createProgressProject(payload: ProgressProjectCreatePayload) {
  return unwrap<{ projectTemplateId: number; projectCode: string; projectName: string }>(http.post("/progress/projects", payload));
}

export function getProgressMatrix(projectTemplateId: number) {
  return unwrap<ProgressMatrixResponse>(http.get(`/progress/projects/${projectTemplateId}/matrix`));
}

export function analyzeProgressMatrix(projectTemplateId: number) {
  return unwrap<ProgressMatrixAiAnalysis>(http.post(`/progress/projects/${projectTemplateId}/ai-analysis`));
}

export function getProgressBrokers() {
  return unwrap<ProgressBrokerSimple[]>(http.get("/progress/brokers"));
}

export function addProgressProjectBrokers(projectTemplateId: number, payload: ProgressProjectBrokerAddPayload) {
  return unwrap<{ addedCount: number }>(http.post(`/progress/projects/${projectTemplateId}/brokers`, payload));
}

export function createProgressProjectItem(projectTemplateId: number, payload: ProgressItemTemplateCreatePayload) {
  return unwrap<{ itemTemplateId: number; itemKey: string; itemLabel: string }>(http.post(`/progress/projects/${projectTemplateId}/items`, payload));
}

export function updateProgressProjectItem(projectTemplateId: number, itemTemplateId: number, payload: ProgressItemTemplateCreatePayload) {
  return unwrap<{ itemTemplateId: number }>(http.put(`/progress/projects/${projectTemplateId}/items/${itemTemplateId}`, payload));
}

export function deleteProgressProjectItem(projectTemplateId: number, itemTemplateId: number) {
  return unwrap<{ deleted: boolean }>(http.delete(`/progress/projects/${projectTemplateId}/items/${itemTemplateId}`));
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

export function updateProgressLog(logId: number, payload: ProgressLogCreatePayload) {
  return unwrap(http.put(`/progress/logs/${logId}`, payload));
}

export function createProgressRisk(instanceId: number, payload: ProgressRiskCreatePayload) {
  return unwrap(http.post(`/progress/instances/${instanceId}/risks`, payload));
}

export function updateProgressRisk(riskId: number, payload: ProgressRiskUpdatePayload) {
  return unwrap(http.put(`/progress/risks/${riskId}`, payload));
}

export function createProgressTask(instanceId: number, payload: ProgressTaskCreatePayload) {
  return unwrap<{ id: number }>(http.post(`/progress/instances/${instanceId}/tasks`, payload));
}

export function updateProgressTask(taskId: number, payload: ProgressTaskUpdatePayload) {
  return unwrap<{ id: number }>(http.put(`/progress/tasks/${taskId}`, payload));
}

export function completeProgressTask(taskId: number, payload: ProgressTaskStatusPayload) {
  return unwrap<{ id: number }>(http.post(`/progress/tasks/${taskId}/complete`, payload));
}

export function blockProgressTask(taskId: number, payload: ProgressTaskStatusPayload) {
  return unwrap<{ id: number }>(http.post(`/progress/tasks/${taskId}/block`, payload));
}

export function deleteProgressTask(taskId: number) {
  return unwrap<{ deleted: boolean }>(http.delete(`/progress/tasks/${taskId}`));
}

export function updateProgressStage2Step(instanceId: number, stepInstanceId: number, payload: ProgressStage2StepUpdatePayload) {
  return unwrap(http.post(`/progress/instances/${instanceId}/stage2/steps/${stepInstanceId}/update`, payload));
}

export function createProgressStage2Step(instanceId: number, payload: ProgressStage2StepCreatePayload) {
  return unwrap<{ stepInstanceId: number }>(http.post(`/progress/instances/${instanceId}/stage2/steps`, payload));
}

export function moveProgressStage2Step(instanceId: number, stepInstanceId: number, payload: ProgressStage2StepMovePayload) {
  return unwrap<{ moved: boolean }>(http.post(`/progress/instances/${instanceId}/stage2/steps/${stepInstanceId}/move`, payload));
}

export function deleteProgressStage2Step(instanceId: number, stepInstanceId: number) {
  return unwrap<{ deleted: boolean }>(http.delete(`/progress/instances/${instanceId}/stage2/steps/${stepInstanceId}`));
}
